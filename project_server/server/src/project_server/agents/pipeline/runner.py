import uuid
from typing import Optional, List
from pydantic_ai.agent import AgentRunResult

from project_server.file_manager import file_manager
from project_server.agents.pipeline.agent import pipeline_agent
from project_server.agents.pipeline.prompt import PIPELINE_AGENT_SYSTEM_PROMPT
from project_server.agents.pipeline.output import (
    FunctionsToImplementOutput,
    DetailedFunctionDescription,
    ImplementationFeedbackOutput,
    submit_detailed_function_description_output,
    submit_final_pipeline_output
)
from project_server.agents.swe.runner import SWEAgentRunner
from project_server.worker import broker, logger
from project_server.app_secrets import SWE_MAX_TRIES
from project_server.client import (
    post_run,
    patch_run_status,
    post_add_entity,
    post_create_node,
    post_pipeline,
    post_function,
    post_search_functions,
    post_run_message_pydantic
)

from project_server.agents.runner_base import RunnerBase

from synesis_schemas.main_server import (
    RunCreate,
    RunMessageCreatePydantic,
    RunStatusUpdate,
    PipelineCreate,
    FunctionCreate,
    AddEntityToProject,
    FrontendNodeCreate,
    SearchFunctionsRequest,
    QueryRequest
)


class PipelineAgentRunner(RunnerBase):

    def __init__(
            self,
            user_id: str,
            project_id: uuid.UUID,
            conversation_id: uuid.UUID,
            bearer_token: str,
            run_id: Optional[uuid.UUID] = None):

        super().__init__(pipeline_agent, user_id, bearer_token, run_id)
        self.project_id = project_id
        self.conversation_id = conversation_id
        self.tries = 0
        self.swe_runner = None

    async def __call__(self, prompt_content: str) -> PipelineCreate:

        try:
            if self.run_id is None:
                run = await post_run(self.project_client, RunCreate(type="pipeline", conversation_id=self.conversation_id))
                self.run_id = run.id

            search_run = await self.agent.run(
                "Now search for relevant functions!",
                output_type=List[QueryRequest],
                message_history=self.message_history
            )

            self.message_history += search_run.new_messages()

            await self._log_message_to_redis("Searching knowledge bank", "result", write_to_db=True)

            search_response = await post_search_functions(self.project_client, SearchFunctionsRequest(
                queries=search_run.output
            ))

            logger.info(f"Function search results: {search_response.results}")

            pipeline_run_result = await self._run_agent(
                f"The search results are:\n\n{search_response.results}\n\n" +
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

                    fn_spec_run_result = await self._run_agent(
                        f"We are currently looking at the function '{fn_name}'\n" +
                        f"A brief description of the function is:\n\n{fn_desc}\n\n" +
                        "Please create a detailed implementation spec for the software engineer agent.\n",
                        output_type=submit_detailed_function_description_output,
                        message_history=self.message_history
                    )

                    fn_spec_output: DetailedFunctionDescription = fn_spec_run_result.output

                    self.message_history += fn_spec_run_result.new_messages()

                    input_structure_ids = [
                        input.structure_id for input in fn_spec_output.input_structures
                    ]

                    output_structure_ids = [
                        output.structure_id for output in fn_spec_output.output_structures
                    ]

                    deliverable_description = (
                        "I have been tasked to compose a data processing pipeline. For context, this is my full task description:\n\n" +
                        f"'{PIPELINE_AGENT_SYSTEM_PROMPT}'\n\n" +
                        f"Now I need you to implement a function as part of the pipeline. You need to implement:\n\n{fn_spec_output.model_dump_json()}\n\n" +
                        "Go!"
                    )

                    implementation_approved = False

                    swe_prompt = deliverable_description

                    await self._log_message_to_redis("Calling SWE agent to implement function", "result", write_to_db=True)

                    self.swe_runner = SWEAgentRunner(
                        self.user_id,
                        self.bearer_token,
                        self.conversation_id,
                        self.run_id,
                        structure_ids_to_inject=input_structure_ids+output_structure_ids
                    )

                    self.tries = 0

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

                        logger.info(f"Feedback prompt: {feedback_prompt}")

                        feedback_run = await self._run_agent(
                            feedback_prompt,
                            output_type=ImplementationFeedbackOutput,
                            message_history=self.message_history
                        )

                        self.message_history += feedback_run.new_messages()

                        implementation_approved = feedback_run.output.approved
                        swe_prompt = feedback_run.output.feedback

                        logger.info(
                            f"Implementation approved: {implementation_approved}")
                        logger.info(f"Feedback: {swe_prompt}")

                        if implementation_approved:

                            await self._log_message_to_redis("Implementation approved, saving function", "result", write_to_db=True)

                            # Should maybe use the actual function ID, for now we must use the file paths fetched from the main server to get the functions
                            save_dir_id = uuid.uuid4()

                            implementation_script_path = file_manager.save_function_script(
                                save_dir_id,
                                "implementation.py",
                                swe_result.implementation.script
                            )

                            if swe_result.setup:
                                setup_script_path = file_manager.save_function_script(
                                    save_dir_id,
                                    "setup.sh",
                                    swe_result.setup.script
                                )
                            else:
                                setup_script_path = None

                            fn_response = await post_function(self.project_client, FunctionCreate(
                                name=fn_name,
                                description=fn_spec_output.description,
                                implementation_script_path=str(
                                    implementation_script_path),
                                setup_script_path=str(
                                    setup_script_path) if setup_script_path else None,
                                default_config=swe_result.config.config_dict if swe_result.config else None,
                                type=fn_spec_output.type,
                                input_structures=[inp.model_dump()
                                                  for inp in fn_spec_output.input_structures],
                                output_structures=[out.model_dump()
                                                   for out in fn_spec_output.output_structures],
                                output_variables=[out.model_dump()
                                                  for out in fn_spec_output.output_variables]
                            ))

                            fn_name_to_function_id[fn_name] = fn_response.id

                        else:
                            await self._log_message_to_redis(
                                f"Implementation rejected. Feedback: {swe_prompt}", "result", write_to_db=True)

                await self._log_message_to_redis("All functions implemented, submitting pipeline", "result", write_to_db=True)

                final_pipeline_run_result = await self._run_agent(
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

    async def _save_results(self, result: AgentRunResult):

        output: PipelineCreate = result.output
        pipeline_response = await post_pipeline(self.project_client, output)

        await post_add_entity(self.project_client, AddEntityToProject(
            project_id=self.project_id,
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
        conversation_id: uuid.UUID,
        prompt_content: str,
        bearer_token: str):

    runner = PipelineAgentRunner(
        user_id, project_id, conversation_id, bearer_token)

    await runner(prompt_content)
