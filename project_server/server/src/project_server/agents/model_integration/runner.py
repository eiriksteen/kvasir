import uuid
from typing import Optional
from pydantic_ai.agent import AgentRunResult

from project_server.file_manager import file_manager
from project_server.agents.model_integration.agent import model_integration_agent
from project_server.agents.model_integration.prompt import MODEL_INTEGRATION_AGENT_SYSTEM_PROMPT
from project_server.agents.model_integration.output import ModelDescription, ImplementationFeedbackOutput
from project_server.agents.swe.runner import SWEAgentRunner
from project_server.worker import broker, logger
from project_server.app_secrets import SWE_MAX_TRIES
from project_server.client import (
    post_run,
    patch_run_status,
    post_add_entity,
    post_create_node,
    post_function,
    post_model,
    post_run_message_pydantic,
    post_model_entity,
    get_model_source,
    post_model_source,
    post_search_model_sources
)

from project_server.agents.runner_base import RunnerBase

from synesis_schemas.main_server import (
    RunCreate,
    RunMessageCreatePydantic,
    RunStatusUpdate,
    AddEntityToProject,
    FrontendNodeCreate,
    FunctionCreate,
    ModelCreate,
    ModelEntityCreate,
    SearchModelSourcesRequest,
    ModelSourceCreate,
    SUPPORTED_MODEL_SOURCES
)


class ModelIntegrationAgentRunner(RunnerBase):

    def __init__(
            self,
            user_id: str,
            project_id: uuid.UUID,
            conversation_id: uuid.UUID,
            bearer_token: str,
            source_id: Optional[uuid.UUID] = None,
            run_id: Optional[uuid.UUID] = None,
            create_model_entity_on_completion: bool = True,
            public: bool = False
    ):

        super().__init__(model_integration_agent, user_id, bearer_token, run_id)
        self.project_id = project_id
        self.conversation_id = conversation_id
        self.tries = 0
        self.swe_runner = None
        self.create_model_entity_on_completion = create_model_entity_on_completion
        self.source_id = source_id
        self.public = public

    async def __call__(
        self,
        prompt_content: str
    ) -> ModelDescription:

        try:
            if self.run_id is None:
                run = await post_run(self.project_client, RunCreate(type="model_integration", conversation_id=self.conversation_id))
                self.run_id = run.id

            if self.source_id is not None:
                model_source = await get_model_source(self.project_client, self.source_id)
            else:
                search_query_run = await self.agent.run(
                    f"The available source types are: {SUPPORTED_MODEL_SOURCES}\n\nNow search for relevant model sources!",
                    output_type=SearchModelSourcesRequest,
                    message_history=self.message_history
                )

                model_source_query_result = await post_search_model_sources(self.project_client, search_query_run.output)

                self.message_history += search_query_run.new_messages()

                model_source_selection_run = await self._run_agent(
                    f"Here are the sources we found: {[r.model_dump_json() for r in model_source_query_result]}\n\n" +
                    "Now, if we can use one of the sources, output the source ID, otherwise, output the necessary information to create a new source!",
                    output_type=[uuid.UUID, ModelSourceCreate],
                    message_history=self.message_history
                )

                if isinstance(model_source_selection_run.output, uuid.UUID):
                    model_source = await get_model_source(self.project_client, model_source_selection_run.output)
                else:
                    selection = model_source_selection_run.output
                    selection.public = self.public
                    model_source = await post_model_source(self.project_client, selection)

            model_spec_run_result = await self._run_agent(
                f"This is the model description '{prompt_content}'\n" +
                f"The source of the model is {model_source}\n" +
                "Now, using provided tools or your own knowledge, create a detailed implementation spec for the model.\n",
                output_type=ModelDescription,
                message_history=self.message_history
            )

            model_spec_output: ModelDescription = model_spec_run_result.output

            self.message_history += model_spec_run_result.new_messages()

            swe_prompt = (
                "I have been tasked to build a production ready ML model. For context, this is my full task description:\n\n" +
                f"'{MODEL_INTEGRATION_AGENT_SYSTEM_PROMPT}'\n\n" +
                f"Now I need you to implement the model. This is the spec:\n\n{model_spec_output.model_dump_json()}\n\n" +
                "Give the functions the names specified in the spec." +
                "Let's start with the training function. Go!"
            )

            for function_type in ["training", "inference"]:

                input_structure_ids = [
                    input.structure_id for input in model_spec_output.training_function.input_structures
                ]

                output_structure_ids = [
                    output.structure_id for output in model_spec_output.training_function.output_structures
                ]

                await self._log_message_to_redis(f"Calling SWE agent to implement {function_type} function", "result", write_to_db=True)

                self.swe_runner = SWEAgentRunner(
                    self.user_id,
                    self.bearer_token,
                    self.conversation_id,
                    self.run_id,
                    structure_ids_to_inject=input_structure_ids+output_structure_ids
                )

                self.tries = 0
                implementation_approved = False
                fn_type_to_function_id = {}

                while not implementation_approved:

                    if self.tries >= SWE_MAX_TRIES:
                        raise RuntimeError(
                            f"SWE agent failed to implement model {model_spec_output.name} after {SWE_MAX_TRIES} tries")

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

                        fn_spec = model_spec_output.training_function if function_type == "training" else model_spec_output.inference_function

                        fn_response = await post_function(self.project_client, FunctionCreate(
                            name=fn_spec.name,
                            description=fn_spec.description,
                            implementation_script_path=str(
                                implementation_script_path),
                            setup_script_path=str(
                                setup_script_path) if setup_script_path else None,
                            default_args=swe_result.config.config_dict if swe_result.config else None,
                            type=function_type,
                            input_structures=[inp.model_dump()
                                              for inp in fn_spec.input_structures],
                            output_structures=[out.model_dump()
                                               for out in fn_spec.output_structures],
                            output_variables=[out.model_dump()
                                              for out in fn_spec.output_variables]
                        ))

                        fn_type_to_function_id[function_type] = fn_response.id

                    else:
                        await self._log_message_to_redis(
                            f"Implementation rejected. Feedback: {swe_prompt}", "result", write_to_db=True)

        except Exception as e:
            await patch_run_status(self.project_client, RunStatusUpdate(
                run_id=self.run_id,
                status="failed"
            ))

            await self._log_message_to_redis(f"Error running model integration: {e}", "error", write_to_db=True)
            logger.error(f"Error running model integration: {e}")
            raise e

    async def _save_results(self, result: AgentRunResult, training_function_id: uuid.UUID, inference_function_id: uuid.UUID, model_source_id: uuid.UUID):
        model_spec_output: ModelDescription = result.output

        model_response = await post_model(self.project_client, ModelCreate(
            name=model_spec_output.name,
            description=model_spec_output.description,
            training_function_id=training_function_id,
            inference_function_id=inference_function_id,
            default_config=model_spec_output.model_config,
            public=self.public,
            modality=model_spec_output.modality,
            source_id=model_source_id,
            programming_language_with_version=model_spec_output.programming_language_with_version,
            task=model_spec_output.task
        ))

        await post_run_message_pydantic(self.project_client, RunMessageCreatePydantic(
            run_id=self.run_id,
            content=result.all_messages_json()
        ))

        await patch_run_status(self.project_client, RunStatusUpdate(
            run_id=self.run_id,
            status="completed"
        ))

        if self.create_model_entity_on_completion:

            await post_model_entity(self.project_client, ModelEntityCreate(
                model_id=model_response.id,
                project_id=self.project_id,
                weights_save_dir=None,
                pipeline_id=None,
                config=model_spec_output.model_config
            ))

            await post_add_entity(self.project_client, AddEntityToProject(
                project_id=self.project_id,
                entity_type="model",
                entity_id=model_response.id
            ))

            await post_create_node(self.project_client, FrontendNodeCreate(
                project_id=self.project_id,
                type="model",
                model_id=model_response.id
            ))


@broker.task(retry_on_error=False)
async def run_model_integration_task(
        user_id: uuid.UUID,
        project_id: uuid.UUID,
        conversation_id: uuid.UUID,
        prompt_content: str,
        bearer_token: str,
        public: bool,
        source_id: Optional[uuid.UUID] = None
):

    runner = ModelIntegrationAgentRunner(
        user_id=user_id,
        project_id=project_id,
        conversation_id=conversation_id,
        bearer_token=bearer_token,
        public=public,
        source_id=source_id
    )

    await runner(prompt_content)
