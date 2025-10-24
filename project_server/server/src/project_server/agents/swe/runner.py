import uuid
import docker
from pathlib import Path
from typing import Optional, List

from project_server.agents.swe.agent import swe_agent
from project_server.agents.swe.output import (
    Implementation,
    FunctionImplementationSummary,
    FunctionUpdateOutput,
    ModelUpdateOutput,
    ModelImplementationSummary,
    submit_implementation_output,
    ImplementationSummaryOutputWithImplementation
)
from project_server.agents.swe.deps import SWEAgentDeps
from project_server.client import (
    get_model_entities_by_ids,
    get_data_sources_by_ids,
    get_datasets_by_ids,
    post_pipeline_implementation,
    post_add_entity,
    post_function,
    post_update_function,
    post_update_model,
    post_model,
    post_model_entity_implementation,
    get_analyses_by_ids
)
from project_server.agents.runner_base import RunnerBase
from project_server.entity_manager import script_manager
from synesis_schemas.main_server import (
    GetModelEntityByIDsRequest,
    GetDataSourcesByIDsRequest,
    GetDatasetsByIDsRequest,
    GetAnalysesByIDsRequest,
    FunctionCreate,
    ScriptCreate,
    ModelUpdateCreate,
    Function,
    ModelImplementation,
    ModelEntity,
    FunctionUpdateCreate,
    PipelineCreate,
    AddEntityToProject,
    ModelImplementationCreate,
    PipelineImplementationCreate,
    ModelEntityImplementationCreate,
    ModelEntityCreate,
)
from project_server.agents.swe.sandbox_code import add_submit_pipeline_result_code_to_implementation
from project_server.worker import broker
from synesis_schemas.project_server import RunSWERequest


class SWEAgentRunner(RunnerBase):

    def __init__(
            self,
            user_id: str,
            bearer_token: str,
            project_id: uuid.UUID,
            conversation_id: Optional[uuid.UUID] = None,
            run_id: Optional[uuid.UUID] = None,
            target_pipeline_id: Optional[uuid.UUID] = None,
            log: bool = False,
            input_data_source_ids: Optional[List[uuid.UUID]] = None,
            input_dataset_ids: Optional[List[uuid.UUID]] = None,
            input_analysis_ids: Optional[List[uuid.UUID]] = None,
            input_model_entity_ids: Optional[List[uuid.UUID]] = None,
    ):

        super().__init__(
            agent=swe_agent,
            user_id=user_id,
            bearer_token=bearer_token,
            run_id=run_id,
            run_type="swe",
            conversation_id=conversation_id,
            project_id=project_id,
        )

        self.container = None
        self.log = log
        self.container_name = "project-sandbox"
        self.container_cwd = Path("/app")
        self.target_pipeline_id = target_pipeline_id

        self.input_data_source_ids = input_data_source_ids
        self.input_dataset_ids = input_dataset_ids
        self.input_analysis_ids = input_analysis_ids
        self.input_model_entity_ids = input_model_entity_ids

        self.model_entities = None
        self.data_sources = None
        self.datasets = None
        self.functions = None

        # TODO: Implement these
        self.new_container_created = False
        ##

        self.base_image = "project-sandbox"
        self.docker_client = docker.from_env()

    async def __call__(self, prompt_content: str) -> ImplementationSummaryOutputWithImplementation:

        try:
            await self._prepare_deps()
            await self._create_run_if_not_exists()
            # await self._setup_container()

            swe_prompt = (
                f"Your instruction is:\n\n'{prompt_content}'\n\n" +
                "Go!"
            )

            run_result = await self._run_agent(
                swe_prompt,
                output_type=[
                    # TODO: Add setup, will need to spin up extra container in this case
                    # submit_setup_output,
                    submit_implementation_output
                ],
                deps=self.deps
            )

            self._cleanup_temporary_scripts(run_result.output)
            await self._save_results(run_result.output)

            if self.log:
                await self._log_message(
                    content=f"Implementation result: {run_result.output.model_dump_json()}",
                    type="result"
                )

            await self._complete_agent_run("SWE agent run completed")

            return run_result.output

        except Exception as e:
            self._delete_temporary_scripts()
            await self._fail_agent_run(f"Error running SWE agent: {e}")
            if self.container and self.new_container_created:
                self.container.stop()
                self.container.remove()
                self.new_container_created = False
            raise e

    def _delete_temporary_scripts(self) -> None:
        # Delete current scripts
        for filename in list(self.deps.current_scripts.keys()):
            script_manager.delete_temporary_script(filename)
        # Delete old scripts
        for filename in list(self.deps.modified_scripts_old_to_new_name.keys()):
            script_manager.delete_temporary_script(filename)

    def _cleanup_temporary_scripts(self, final_result: ImplementationSummaryOutputWithImplementation) -> None:
        self._delete_temporary_scripts()
        implementation_output = final_result.implementation
        implementation_output.main_script.script = script_manager.clean_temporary_script(
            implementation_output.main_script.script)

        for new_script in implementation_output.new_scripts:
            new_script.script = script_manager.clean_temporary_script(
                new_script.script)

        for modified_script in implementation_output.modified_scripts:
            modified_script.original_script = script_manager.clean_temporary_script(
                modified_script.original_script)
            modified_script.new_script = script_manager.clean_temporary_script(
                modified_script.new_script)

    async def _prepare_deps(self) -> None:

        self.data_sources = await get_data_sources_by_ids(self.project_client, GetDataSourcesByIDsRequest(data_source_ids=self.input_data_source_ids))
        self.datasets = await get_datasets_by_ids(self.project_client, GetDatasetsByIDsRequest(dataset_ids=self.input_dataset_ids))
        self.analyses = await get_analyses_by_ids(self.project_client, GetAnalysesByIDsRequest(analysis_ids=self.input_analysis_ids))
        self.model_entities = await get_model_entities_by_ids(self.project_client, GetModelEntityByIDsRequest(model_entity_ids=self.input_model_entity_ids))

        deps = SWEAgentDeps(
            cwd=str(self.container_cwd),
            container_name=self.container_name,
            bearer_token=self.bearer_token,
            client=self.project_client,
            log_code=self._stream_code,
            model_entities_injected=self.model_entities,
            data_sources_injected=self.data_sources,
            datasets_injected=self.datasets,
            analyses_injected=self.analyses,
            conversation_id=self.conversation_id
        )

        if self.model_entities:
            for model_entity in self.model_entities:
                with open(model_entity.implementation.model_implementation.implementation_script.path, "r") as f:
                    script_content = f.read()

                model_storage = script_manager.save_script(
                    model_entity.implementation.model_implementation.implementation_script.filename, script_content, "model", add_uuid=False, temporary=True)

                deps.current_scripts[model_storage.filename] = script_content

        # The functions will be injected when the agent searches for them, as we don't know yet which functions are needed

        self.deps = deps

    def _get_new_functions_create(
        self,
        new_functions: List[FunctionImplementationSummary],
        implementation: Implementation
    ) -> List[FunctionCreate]:

        new_functions_create = []

        for fn_desc in new_functions:
            script = next(
                (res.script for res in implementation.new_scripts if res.filename == fn_desc.filename), None)

            assert script is not None, f"Agent outputted a new script but no script for function {fn_desc.filename} found"

            implementation_storage = script_manager.save_script(
                fn_desc.filename,
                script,
                "function"
            )

            new_function = FunctionCreate(
                **fn_desc.model_dump(),
                implementation_script_create=ScriptCreate(
                    path=str(implementation_storage.script_path),
                    filename=implementation_storage.filename,
                    module_path=implementation_storage.module_path,
                    type="function"
                )
            )

            new_functions_create.append(new_function)

        return new_functions_create

    def _get_new_models_create(
        self,
        new_models: List[ModelImplementationSummary],
        implementation: Implementation
    ) -> List[ModelImplementationCreate]:

        new_models_create = []

        for model_desc in new_models:
            script = next(
                (res.script for res in implementation.new_scripts if res.filename == model_desc.filename), None)

            assert script is not None, f"Agent outputted a new model script but no script for model {model_desc.filename} found"

            implementation_storage = script_manager.save_script(
                model_desc.filename,
                script,
                "model"
            )

            new_models_create.append(ModelImplementationCreate(
                **model_desc.model_dump(),
                public=False,  # TODO: Make this configurable
                implementation_script_create=ScriptCreate(
                    path=str(implementation_storage.script_path),
                    filename=implementation_storage.filename,
                    module_path=implementation_storage.module_path,
                    type="model"
                )
            ))

        return new_models_create

    def _get_function_updates_create(
        self,
        function_updates: List[FunctionUpdateOutput],
        functions_used: List[Function],
        implementation: Implementation
    ) -> List[FunctionUpdateCreate]:

        functions_updated = []

        for fn in functions_used:
            update = next(
                (u for u in function_updates if u.definition_id == fn.definition.id), None)
            if update is not None:
                new_script, new_filename = next(
                    ((res.new_script, res.new_filename)
                     for res in implementation.modified_scripts if res.original_filename == fn.implementation_script.filename), (None, None))

                assert new_script is not None, f"Agent outputted a modification but no new script for function {fn.implementation_script.filename} found"

                implementation_storage = script_manager.save_script(
                    new_filename,
                    new_script,
                    "function"
                )

                functions_updated.append(FunctionUpdateCreate(
                    **update.model_dump(),
                    new_implementation_create=ScriptCreate(
                        path=str(implementation_storage.script_path),
                        filename=implementation_storage.filename,
                        module_path=implementation_storage.module_path,
                        type="function"
                    ),
                ))

        return functions_updated

    def _get_model_updates_create(
        self,
        model_updates: List[ModelUpdateOutput],
        models_used: List[ModelEntity],
        implementation: Implementation
    ) -> List[ModelUpdateCreate]:

        models_updated = []

        for model_entity in models_used:
            update = next(
                (u for u in model_updates if u.definition_id == model_entity.implementation.model_implementation.definition.id), None)
            if update is not None:
                new_script, new_filename = next(
                    ((res.new_script, res.new_filename)
                     for res in implementation.modified_scripts if res.original_filename == model_entity.implementation.model_implementation.implementation_script.filename), (None, None))

                assert new_script is not None, f"Agent outputted a modification but no new script for model {model_entity.implementation.model_implementation.implementation_script.filename} found"

                implementation_storage = script_manager.save_script(
                    new_filename,
                    new_script,
                    "model"
                )

                models_updated.append(ModelUpdateCreate(
                    **update.model_dump(),
                    new_implementation_create=ScriptCreate(
                        path=str(implementation_storage.script_path),
                        filename=implementation_storage.filename,
                        module_path=implementation_storage.module_path,
                        type="model"
                    ),
                    model_entities_to_update=[model_entity.id]
                ))
        return models_updated

    async def _save_results(self, final_result: ImplementationSummaryOutputWithImplementation) -> None:
        # TODO: Add validation to ensure the new scripts don't already exist

        new_function_creates = self._get_new_functions_create(
            final_result.new_supporting_functions, final_result.implementation)

        new_model_creates = self._get_new_models_create(
            final_result.new_models, final_result.implementation)

        new_models: List[ModelImplementation] = []
        for model_create in new_model_creates:
            new_model = await post_model(self.project_client, model_create)
            new_models.append(ModelImplementation(**new_model.model_dump()))

        new_functions = []
        for function_create in new_function_creates:
            new_function = await post_function(self.project_client, function_create)
            new_functions.append(Function(**new_function.model_dump()))

        function_update_creates = self._get_function_updates_create(
            final_result.modified_functions, final_result.functions_used, final_result.implementation)

        for function_update in function_update_creates:
            await post_update_function(self.project_client, function_update)

        model_update_creates = self._get_model_updates_create(
            final_result.modified_models, self.model_entities, final_result.implementation)

        for model_update in model_update_creates:
            await post_update_model(self.project_client, model_update)

        final_script = add_submit_pipeline_result_code_to_implementation(
            final_result.implementation.main_script.script,
            final_result.new_main_function.output_object_group_definitions,
            final_result.new_main_function.output_variables_schema
        )

        pipeline_script = script_manager.save_script(
            f"{final_result.new_main_function.python_function_name}.py", final_script, "pipeline", add_uuid=True, temporary=False)

        # If new models are created, create new model entities for them to be used as inputs to the pipeline

        new_model_entity_ids = []
        for mdl in new_models:
            new_model_entity = await post_model_entity_implementation(self.project_client, ModelEntityImplementationCreate(
                config=mdl.default_config,
                weights_save_dir=None,
                pipeline_id=self.target_pipeline_id,
                model_implementation_id=mdl.id,
                model_entity_create=ModelEntityCreate(
                    name=f"{mdl.definition.name} unfitted",
                    description=mdl.description
                )
            ))

            await post_add_entity(self.project_client, AddEntityToProject(
                project_id=self.project_id,
                entity_type="model_entity",
                entity_id=new_model_entity.id
            ))

            new_model_entity_ids.append(new_model_entity.id)

        if not self.target_pipeline_id:
            pipeline_create = PipelineCreate(
                name=final_result.new_main_function.name,
                description=final_result.new_main_function.description,
                input_data_source_ids=self.input_data_source_ids,
                input_dataset_ids=self.input_dataset_ids,
                input_model_entity_ids=self.input_model_entity_ids+new_model_entity_ids
            )
        else:
            pipeline_create = None

        pipeline_implementation_create = PipelineImplementationCreate(
            **final_result.new_main_function.model_dump(),
            args=final_result.new_main_function.default_args,
            implementation_script_create=ScriptCreate(
                path=str(pipeline_script.script_path),
                filename=pipeline_script.filename,
                module_path=pipeline_script.module_path,
                type="pipeline"
            ),
            function_ids=[
                f.id for f in final_result.functions_used + new_functions],
            pipeline_create=pipeline_create,
            pipeline_id=self.target_pipeline_id
        )

        pipeline_response = await post_pipeline_implementation(self.project_client, pipeline_implementation_create)

        if not self.target_pipeline_id:
            await post_add_entity(self.project_client, AddEntityToProject(
                project_id=self.project_id,
                entity_type="pipeline",
                entity_id=pipeline_response.id
            ))


@broker.task
async def run_swe_task(
    user_id: uuid.UUID,
    bearer_token: str,
    swe_request: RunSWERequest
):
    runner = SWEAgentRunner(
        user_id=user_id,
        bearer_token=bearer_token,
        project_id=swe_request.project_id,
        conversation_id=swe_request.conversation_id,
        run_id=swe_request.run_id,
        target_pipeline_id=swe_request.target_pipeline_id,
        input_data_source_ids=swe_request.input_data_source_ids,
        input_dataset_ids=swe_request.input_dataset_ids,
        input_analysis_ids=swe_request.input_analysis_ids,
        input_model_entity_ids=swe_request.input_model_entity_ids
    )

    await runner(swe_request.prompt_content)
