import uuid
from typing import Literal, Optional
from datetime import datetime, timezone
from pydantic_ai.agent import AgentRunResult

from project_server.redis import get_redis
from project_server.agents.pipeline.agent import pipeline_agent
from project_server.agents.pipeline.prompt import PIPELINE_AGENT_SYSTEM_PROMPT
from project_server.agents.pipeline.output import (
    SearchQueryOutput,
    FunctionsToImplementOutput,
    ImplementationFeedbackOutput,
    FinalPipelineOutput,
    submit_detailed_function_description_output,
    submit_final_pipeline_output
)
from project_server.agents.swe.runner import SWEAgentRunner
from project_server.worker import broker, logger
from project_server.app_secrets import SWE_MAX_TRIES
from synesis_data_structures.time_series.definitions import get_data_structure_description
from project_server.client import (
    ProjectClient,
    post_run,
    post_run_message,
    patch_run_status,
    post_add_entity,
    post_create_node,
    post_pipeline,
    post_function,
    post_search_functions,
    post_run_message_pydantic
)
from synesis_schemas.main_server import (
    RunCreate,
    RunMessageCreate,
    RunMessageCreatePydantic,
    RunStatusUpdate,
    PipelineCreate,
    FunctionCreate,
    AddEntityToProject,
    FrontendNodeCreate,
    SearchFunctionsRequest
)


class PipelineAgentRunner:

    def __init__(
            self,
            user_id: str,
            project_id: uuid.UUID,
            conversation_id: uuid.UUID,
            bearer_token: str,
            run_id: Optional[uuid.UUID] = None):

        self.pipeline_agent = pipeline_agent
        self.user_id = user_id
        self.project_id = project_id
        self.conversation_id = conversation_id
        self.message_history = []
        self.run_id = run_id
        self.tries = 0
        self.bearer_token = bearer_token
        self.project_client = ProjectClient()
        self.project_client.set_bearer_token(bearer_token)

        self.swe_runner = SWEAgentRunner(
            user_id,
            bearer_token,
            conversation_id,
            run_id
        )

        self.redis_stream = get_redis()

    async def __call__(self, prompt_content: str) -> FinalPipelineOutput:

        try:
            if self.run_id is None:
                run = await post_run(self.project_client, RunCreate(type="pipeline"))
                self.run_id = run.id

            search_run = await self.pipeline_agent.run(
                f"The user has submitted this request for building a processing pipeline:\n\n{prompt_content}\n\nNow search for relevant functions!",
                output_type=SearchQueryOutput
            )

            self.message_history += search_run.new_messages()

            await self._log_message_to_redis("Searching knowledge bank", "result", write_to_db=True)

            search_response = await post_search_functions(self.project_client, SearchFunctionsRequest(
                queries=search_run.output.function_descriptions,
                k=10
            ))

            retrieved_functions = search_response.functions

            logger.info(f"RETRIEVED FUNCTIONS: {retrieved_functions}")

            search_result_str = "\n\n".join([
                f"SEARCH RESULTS FOR {search_name}: {fn}"
                for search_name, functions in zip(search_run.output.function_names, retrieved_functions) for fn in functions
            ])

            pipeline_run_result = await self.pipeline_agent.run(
                f"The search results are:\n\n{search_result_str}\n\n" +
                "Now determine whether these suffice to compose the final pipeline, or if new functions must be implemented. " +
                "In case we need new ones, submit descriptions for each.",
                output_type=[
                    FunctionsToImplementOutput,
                    submit_final_pipeline_output
                ],
                message_history=self.message_history
            )

            self.message_history += pipeline_run_result.new_messages()

            if isinstance(pipeline_run_result.output, FunctionsToImplementOutput):

                await self._log_message_to_redis("Implementing functions", "result", write_to_db=True)

                fn_name_to_function_id = {}

                for fn_name, fn_desc in zip(pipeline_run_result.output.function_names, pipeline_run_result.output.function_descriptions_brief):

                    fn_spec_run_result = await self.pipeline_agent.run(
                        f"We are currently looking at the function '{fn_name}'\n" +
                        f"A brief description of the function is:\n\n{fn_desc}\n\n" +
                        "Please create a detailed implementation spec for the software engineer agent.\n",
                        output_type=submit_detailed_function_description_output,
                        message_history=self.message_history

                    )

                    self.message_history += fn_spec_run_result.new_messages()

                    input_structure_ids = [
                        input.structure_id for input in fn_spec_run_result.output.inputs
                    ]

                    output_structure_ids = [
                        output.structure_id for output in fn_spec_run_result.output.outputs
                    ]

                    structure_descriptions = [
                        get_data_structure_description(structure_id) for structure_id in input_structure_ids + output_structure_ids
                    ]

                    deliverable_description = (
                        "I have been tasked to compose a data processing pipeline. For context, this is my full task description:\n\n" +
                        f"'{PIPELINE_AGENT_SYSTEM_PROMPT}'\n\n" +
                        f"Now I need you to implement a function as part of the pipeline. You need to implement:\n\n{fn_spec_run_result.output.model_dump_json()}\n\n" +
                        f"All relevant data structure descriptions for the inputs and outputs are:\n\n{structure_descriptions}\n\n" +
                        "Go!"
                    )

                    implementation_approved = False

                    swe_prompt = deliverable_description

                    await self._log_message_to_redis("Calling SWE agent to implement function", "result", write_to_db=True)

                    while not implementation_approved:

                        if self.tries >= SWE_MAX_TRIES:
                            raise RuntimeError(
                                f"SWE agent failed to implement function {fn_name} after {SWE_MAX_TRIES} tries")

                        self.tries += 1

                        swe_result = await self.swe_runner(swe_prompt)

                        feedback_prompt = (
                            "The software engineer agent has submitted a solution.\n" +
                            f"Its result is:\n\n{swe_result.model_dump_json()}\n\n" +
                            "Decide whether to accept it, or reject it with feedback on what to fix before the solution is approved."
                        )

                        logger.info(f"FEEDBACK PROMPT: {feedback_prompt}")

                        feedback_run = await self.pipeline_agent.run(
                            feedback_prompt,
                            output_type=ImplementationFeedbackOutput,
                            message_history=self.message_history
                        )

                        self.message_history += feedback_run.new_messages()

                        implementation_approved = feedback_run.output.approved
                        swe_prompt = feedback_run.output.feedback

                        logger.info(
                            f"IMPLEMENTATION APPROVED: {implementation_approved}")
                        logger.info(f"FEEDBACK: {swe_prompt}")

                        if implementation_approved:

                            await self._log_message_to_redis("Implementation approved, saving function", "result", write_to_db=True)

                            fn_response = await post_function(self.project_client, FunctionCreate(
                                name=fn_name,
                                description=fn_spec_run_result.output.description,
                                implementation_script=swe_result.implementation.script,
                                setup_script=swe_result.setup.script if swe_result.setup else None,
                                config_dict=swe_result.config.config_dict if swe_result.config else None,
                                inputs=fn_spec_run_result.output.inputs,
                                outputs=fn_spec_run_result.output.outputs
                            ))

                            fn_name_to_function_id[fn_name] = fn_response.id

                            # Reset SWE agent runner to ensure cleared context for the next implementation
                            self.swe_runner = SWEAgentRunner(
                                self.user_id,
                                self.bearer_token,
                                self.conversation_id,
                                self.run_id
                            )

                        else:
                            await self._log_message_to_redis(
                                f"Implementation rejected. Feedback: {swe_prompt}", "result", write_to_db=True)

                await self._log_message_to_redis("All functions implemented, submitting pipeline", "result", write_to_db=True)

                final_pipeline_run_result = await self.pipeline_agent.run(
                    "Now that we have implemented all needed functions, output the IDs in the order they should be called to define the final pipeline " +
                    "(including the IDs of any prebuilt functions you use as part of the pipeline).\n\n" +
                    f"The function name to ID mapping is:\n\n{fn_name_to_function_id}",
                    output_type=submit_final_pipeline_output,
                    message_history=self.message_history
                )

                await self._save_results(final_pipeline_run_result)
                await self._log_message_to_redis("Pipeline complete", "result", write_to_db=True)

                return final_pipeline_run_result.output

            else:
                await self._save_results(pipeline_run_result)
                await self._log_message_to_redis("Using prebuilt functions, submitting pipeline", "result", write_to_db=True)
                logger.info(
                    f"Using prebuilt functions, submitting pipeline: {pipeline_run_result.output.model_dump_json()}")

                return pipeline_run_result.output

        except Exception as e:
            await patch_run_status(self.project_client, RunStatusUpdate(
                run_id=self.run_id,
                status="failed"
            ))

            await self._log_message_to_redis(f"Error running pipeline: {e}", "error", write_to_db=True)
            logger.error(f"Error running pipeline: {e}")
            raise e

    async def _log_message_to_redis(
            self,
            content: str,
            message_type: Literal["tool_call", "result", "error"],
            write_to_db: bool = True
    ):
        """Log a message to Redis stream"""

        message = {
            "id": str(uuid.uuid4()),
            "role": "agent",
            "content": content,
            "run_id": str(self.run_id),
            "type": message_type,
            "created_at": datetime.now(timezone.utc).isoformat()
        }
        await self.redis_stream.xadd(str(self.run_id), message)

        if write_to_db:
            await post_run_message(self.project_client, RunMessageCreate(
                type=message_type,
                run_id=str(self.run_id),
                content=content
            ))

    async def _save_results(self, result: AgentRunResult):

        output: FinalPipelineOutput = result.output

        pipeline_response = await post_pipeline(self.project_client, PipelineCreate(
            name=output.name,
            description=output.description,
            function_ids=[f.id for f in output.functions],
            function_configs=[f.config for f in output.functions],
            periodic_schedules=output.periodic_schedules,
            on_event_schedules=output.on_event_schedules,
        ))

        await post_add_entity(self.project_client, AddEntityToProject(
            entity_type="pipeline",
            entity_id=pipeline_response.id
        ))

        await post_create_node(self.project_client, FrontendNodeCreate(
            project_id=self.project_id,
            type="pipeline",
            pipeline_id=pipeline_response.id
        ))

        await patch_run_status(self.project_client, RunStatusUpdate(
            run_id=self.run_id,
            status="completed"
        ))

        await post_run_message_pydantic(self.project_client, RunMessageCreatePydantic(
            run_id=self.run_id,
            content=result.new_messages_json()
        ))


@broker.task(retry_on_error=False)
async def run_pipeline_task(
        user_id: uuid.UUID,
        project_id: uuid.UUID,
        run_id: uuid.UUID,
        conversation_id: uuid.UUID,
        prompt_content: str,
        bearer_token: str):

    runner = PipelineAgentRunner(
        user_id, project_id, conversation_id, bearer_token, run_id)

    await runner(prompt_content)
