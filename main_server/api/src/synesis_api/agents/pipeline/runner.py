import uuid
from typing import Literal
from datetime import datetime, timezone


from synesis_api.redis import get_redis
from synesis_api.modules.runs.service import create_run_message, create_run, create_run_message_pydantic, update_run_status
from synesis_api.modules.pipeline.service import search_functions, create_function, create_pipeline
from synesis_api.agents.pipeline.agent import pipeline_agent
from synesis_api.agents.pipeline.prompt import PIPELINE_AGENT_SYSTEM_PROMPT
from synesis_api.agents.pipeline.output import (
    SearchQueryOutput,
    FunctionsToImplementOutput,
    ImplementationFeedbackOutput,
    FinalPipelineOutput,
    submit_detailed_function_description_output,
    submit_final_pipeline_output
)
from synesis_api.agents.swe.runner import SWEAgentRunner
from synesis_api.agents.pipeline.validation import validate_script, validate_arg_order
from synesis_api.storage.local import save_script_to_local_storage
from synesis_api.worker import broker, logger
from synesis_api.modules.project.service import add_entity_to_project
from synesis_api.modules.node.service import create_node
from synesis_api.modules.node.schema import FrontendNodeCreate
from synesis_api.modules.project.schema import AddEntityToProject
from synesis_api.app_secrets import SWE_MAX_TRIES
from synesis_data_structures.time_series.definitions import get_data_structure_description


class PipelineAgentRunner:

    def __init__(
            self,
            user_id: str,
            project_id: uuid.UUID,
            conversation_id: uuid.UUID,
            run_id: uuid.UUID
    ):

        self.pipeline_agent = pipeline_agent
        self.user_id = user_id
        self.project_id = project_id
        self.conversation_id = conversation_id
        self.message_history = []
        self.run_id = run_id
        self.tries = 0

        self.swe_runner = SWEAgentRunner(
            user_id,
            conversation_id,
            run_id,
            implementation_validation_fns=[
                validate_script,
                validate_arg_order
            ])

        self.redis_stream = get_redis()

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
            await create_run_message(message_type, self.run_id, content)

    async def _save_results(self, result: FinalPipelineOutput):

        pipeline = await create_pipeline(
            name=result.name,
            description=result.description,
            user_id=self.user_id,
            function_ids=[f.id for f in result.functions],
            function_configs=[f.config for f in result.functions],
            periodic_schedules=result.periodic_schedules,
            on_event_schedules=result.on_event_schedules
        )

        await add_entity_to_project(self.project_id, AddEntityToProject(entity_type="pipeline", entity_id=pipeline.id))
        await create_node(FrontendNodeCreate(project_id=self.project_id, type="pipeline", pipeline_id=pipeline.id))

        # TODO: Save run-specific results also

    async def __call__(self, prompt_content: str) -> FinalPipelineOutput:

        try:

            search_run = await self.pipeline_agent.run(
                f"The user has submitted this request for building a processing pipeline:\n\n{prompt_content}\n\nNow search for relevant functions!",
                output_type=SearchQueryOutput
            )

            self.message_history += search_run.new_messages()

            await self._log_message_to_redis("Searching knowledge bank", "result", write_to_db=True)

            retrieved_functions = [
                await search_functions(fn_desc, k=10)
                for fn_desc in search_run.output.function_descriptions
            ]

            logger.info(f"RETRIEVED FUNCTIONS: {retrieved_functions}")

            search_result_str = "\n\n".join([
                f"SEARCH RESULTS FOR {search_name}: {function.model_dump_json(indent=2)}"
                for search_name, functions in zip(search_run.output.function_names, retrieved_functions) for function in functions
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

                    structure_descriptions = [get_data_structure_description(
                        structure_id) for structure_id in input_structure_ids + output_structure_ids
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

                            fn = await create_function(
                                name=fn_name,
                                user_id=self.user_id,
                                run_id=self.run_id,
                                description=fn_spec_run_result.output.description,
                                implementation_script=swe_result.implementation.script,
                                setup_script=swe_result.setup.script if swe_result.setup else None,
                                config_dict=swe_result.config.config_dict if swe_result.config else None,
                                inputs=fn_spec_run_result.output.inputs,
                                outputs=fn_spec_run_result.output.outputs
                            )

                            fn_name_to_function_id[fn_name] = fn.id

                            # Reset SWE agent runner to ensure cleared context for the next implementation
                            self.swe_runner = SWEAgentRunner(
                                self.user_id,
                                self.conversation_id,
                                self.run_id,
                                implementation_validation_fns=[
                                    validate_script,
                                    validate_arg_order
                                ])

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

                await self._save_results(final_pipeline_run_result.output)
                await update_run_status(self.run_id, "completed")
                await self._log_message_to_redis("Pipeline complete", "result", write_to_db=True)

                return final_pipeline_run_result.output

            else:
                await self._save_results(pipeline_run_result.output)
                await update_run_status(self.run_id, "completed")
                await self._log_message_to_redis("Using prebuilt functions, submitting pipeline", "result", write_to_db=True)
                logger.info(
                    f"Using prebuilt functions, submitting pipeline: {pipeline_run_result.output.model_dump_json()}")

                return pipeline_run_result.output

        except Exception as e:
            await update_run_status(self.run_id, "failed")
            await self._log_message_to_redis(f"Error running pipeline: {e}", "error", write_to_db=True)
            logger.error(f"Error running pipeline: {e}")
            raise e


@broker.task(retry_on_error=False)
async def run_pipeline_task(
        user_id: uuid.UUID,
        project_id: uuid.UUID,
        run_id: uuid.UUID,
        conversation_id: uuid.UUID,
        prompt_content: str):

    runner = PipelineAgentRunner(user_id, project_id, conversation_id, run_id)

    await runner(prompt_content)
