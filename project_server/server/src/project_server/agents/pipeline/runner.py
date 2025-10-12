import uuid
from pathlib import Path
from typing import List, Tuple

from project_server.entity_manager import file_manager
from project_server.agents.pipeline.agent import pipeline_agent
from project_server.agents.pipeline.deps import PipelineAgentDeps
from project_server.agents.pipeline.prompt import PIPELINE_AGENT_SYSTEM_PROMPT
from project_server.agents.pipeline.output import (
    FunctionsInPipelineOutput,
    FunctionImplementationSpec,
    ImplementationFeedbackOutput,
    submit_pipeline_spec_output,
    PipelineGraphOutput,
    SearchFunctionsOutput,
    PipelineImplementationSpec,
    ModelConfiguration,
    FunctionUpdateOutput,
    ModelUpdateOutput
)
from project_server.agents.swe.runner import SWEAgentRunner, SWEAgentOutput
from project_server.agents.swe.deps import FunctionToInject, ModelToInject
from project_server.worker import broker
from project_server.app_secrets import SWE_MAX_TRIES
from project_server.client import (
    post_add_entity,
    post_create_node,
    post_pipeline,
    post_search_functions,
    get_datasets_by_ids,
    get_model_entities_by_ids,
    post_function,
    post_update_function,
    patch_model_entity_config,
    post_update_model
)
from project_server.agents.runner_base import RunnerBase
from project_server.agents.pipeline.sandbox_code import create_final_pipeline_script, create_test_code_from_spec

from synesis_schemas.main_server import (
    PipelineCreate,
    FunctionCreate,
    AddEntityToProject,
    FrontendNodeCreate,
    GetDatasetByIDsRequest,
    GetModelEntityByIDsRequest,
    FunctionFull,
    FunctionUpdateCreate,
    ModelEntityWithModelDef,
    # ModelEntityConfigUpdate,
    PipelineNodeCreate,
    PipelineGraphCreate,
    Dataset,
    PipelineInDB,
    ModelUpdateCreate
)


class PipelineAgentRunner(RunnerBase):

    def __init__(
            self,
            user_id: str,
            project_id: uuid.UUID,
            conversation_id: uuid.UUID,
            run_id: uuid.UUID,
            bearer_token: str,
            input_dataset_ids: List[uuid.UUID],
            input_model_entity_ids: List[uuid.UUID] = []):

        super().__init__(agent=pipeline_agent,
                         user_id=user_id,
                         bearer_token=bearer_token,
                         run_id=run_id,
                         project_id=project_id,
                         run_type="pipeline",
                         conversation_id=conversation_id)

        self.input_dataset_ids = input_dataset_ids
        self.input_model_entity_ids = input_model_entity_ids
        self.tries = 0

        self.input_datasets: List[Dataset] = []
        self.input_model_entities: List[ModelEntityWithModelDef] = []

    async def __call__(self, prompt_content: str) -> PipelineInDB:

        try:
            await self._create_run_if_not_exists()

            functions_to_use = await self._run_search_stage(prompt_content)
            await self._run_model_configuration_stage()
            _, pipeline_implementation = await self._run_pipeline_implementation_stage(functions_to_use)
            new_functions, function_updates, model_updates, pipeline_graph, final_spec = await self._run_pipeline_implementation_summary_stage()

            result = await self._save_results(functions_to_use, new_functions, final_spec, pipeline_implementation, function_updates, model_updates, pipeline_graph)
            await self._complete_agent_run("Pipeline agent run completed")

            return result

        except Exception as e:
            await self._fail_agent_run(f"Error running pipeline agent: {e}")
            raise e

    async def _run_search_stage(self, prompt_content: str) -> List[FunctionFull]:
        # Searches for existing functions, outputs the results

        self.input_datasets = await get_datasets_by_ids(self.project_client, GetDatasetByIDsRequest(dataset_ids=self.input_dataset_ids, include_features=True))
        self.input_model_entities = await get_model_entities_by_ids(self.project_client, GetModelEntityByIDsRequest(model_entity_ids=self.input_model_entity_ids))

        await self._log_message(
            f"Input datasets:\n\n{[ds.model_dump_json() for ds in self.input_datasets]}", "result", write_to_db=True)
        await self._log_message(
            f"Input model entities:\n\n{[me.model_dump_json() for me in self.input_model_entities]}", "result", write_to_db=True)

        search_run = await self._run_agent(
            f"The user has requested a pipeline with the following description: {prompt_content}\n\n" +
            f"The input datasets are (pay attention to the df schema and head fields to understand the data you are working with):\n\n{[ds.model_dump_json() for ds in self.input_datasets]}\n\n" +
            f"The input model entities are:\n\n{[me.model_dump_json() for me in self.input_model_entities]}\n\n" +
            "Now search for any relevant functions! If the model functions suffice, you can output an empty list.",
            output_type=SearchFunctionsOutput,
            deps=PipelineAgentDeps(client=self.project_client)
        )

        search_output: SearchFunctionsOutput = search_run.output

        if search_output.query_request:
            await self._log_message("Searching knowledge bank", "result", write_to_db=True)
            search_response = await post_search_functions(self.project_client, search_output.query_request)
            await self._log_message(f"Function search results: {search_response}", "result", write_to_db=True)
        else:
            search_response = []

        functions_to_use_run = await self._run_agent(
            f"The search results are:\n\n{search_response}\n\n" +
            "Now determine which, if any, of the existing functions to use. Output the python function names of the functions to use. ",
            output_type=FunctionsInPipelineOutput,
            deps=PipelineAgentDeps(client=self.project_client)
        )

        pipeline_output: FunctionsInPipelineOutput = functions_to_use_run.output

        existing_functions = []
        if pipeline_output.existing_functions_to_use_names:
            for fn_name in pipeline_output.existing_functions_to_use_names:
                existing_function = next(
                    fn for query_result in search_response for fn in query_result.functions if fn.python_function_name == fn_name
                )

                if not existing_function:
                    raise RuntimeError(
                        f"Agent selected function '{fn_name}' that does not exist in the search results.")

                existing_functions.append(existing_function)

        return existing_functions

    async def _run_model_configuration_stage(self) -> List[ModelConfiguration]:
        # Outputs the model configurations

        fitted_models = [
            me for me in self.input_model_entities if me.weights_save_dir is not None]

        if len(fitted_models) > 0:
            await self._log_message("Checking compatibility with models", "result", write_to_db=True)

            fitted_models_run = await self._run_agent(
                "Now, we must determine whether the fitted model configurations work with the pipeline requirements. " +
                f"The fitted models and their configurations are: {'\n\n'.join([str({me.name: me.config}) for me in fitted_models])}" +
                "Output True if the fitted models configurations work with the pipeline requirements, False otherwise.",
                output_type=bool,
                deps=PipelineAgentDeps(client=self.project_client)
            )

            if not fitted_models_run.output:
                # TODO: Implement mechanism for the agent to communicate with the orchestrator to let it know about this here
                raise RuntimeError(
                    "Fitted models configurations do not work with the pipeline requirements")

        models_unfitted = [
            me for me in self.input_model_entities if me.weights_save_dir is None]

        configurations: List[ModelConfiguration] = []
        if len(models_unfitted) > 0:
            await self._log_message("Configuring model(s)", "result", write_to_db=True)

            model_configurations_run = await self._run_agent(
                "Now, we must determine the configurations for the unfitted models to enable using them in the pipeline. " +
                "For the fixed parameters that should not be tuned, if the user has not provided a value, use reasonable default values which can be extracted through the get guidelines tool. " +
                f"The unfitted models and their default configurations are: {'\n\n'.join(
                    [str({me.name: {'config': me.config}}) for me in models_unfitted])}" +
                "Output the new configurations for each of the models.",
                output_type=List[ModelConfiguration],
                deps=PipelineAgentDeps(client=self.project_client)
            )

            assert len(model_configurations_run.output) == len(models_unfitted)
            configurations = model_configurations_run.output

            for config in configurations:
                model_entity_id = next(
                    me.id for me in self.input_model_entities if me.name == config.model_entity_name)
                updated_model = await patch_model_entity_config(self.project_client, model_entity_id, config.update)

                for me in self.input_model_entities:
                    if me.id == updated_model.id:
                        me.config = updated_model.config
                        break

        return configurations

    async def _run_pipeline_implementation_stage(
        self,
        functions_to_use: List[FunctionFull]
    ) -> Tuple[PipelineImplementationSpec, SWEAgentOutput]:
        # Composes the full pipeline script, evaluates the results, modifies the functions if necessary, saves the pipeline and updated functions

        pipeline_spec_run = await self._run_agent(
            "It is time to compose the final pipeline. " +
            "We will dispatch the software engineer agent to implement the pipeline. " +
            "Now provide a detailed implementation spec for the software engineer agent.",
            output_type=submit_pipeline_spec_output,
            deps=PipelineAgentDeps(client=self.project_client)
        )

        def _extract_structure_ids_from_functions(functions: List[FunctionFull]) -> List[str]:
            return list(set([
                input.structure_id for function in functions for input in function.input_object_groups
            ] + [
                output.structure_id for function in functions for output in function.output_object_groups
            ]))

        structure_ids_to_inject = _extract_structure_ids_from_functions(
            functions_to_use)

        functions_to_inject = [FunctionToInject(
            filename=function.filename,
            script_path=function.implementation_script_path,
            docstring=function.docstring,
            module=function.module_path
        ) for function in functions_to_use]

        models_to_inject = [ModelToInject(
            filename=model_entity.model.filename,
            script_path=model_entity.model.implementation_script_path,
            training_function_docstring=model_entity.model.training_function.docstring,
            inference_function_docstring=model_entity.model.inference_function.docstring,
            model_class_docstring=model_entity.model.model_class_docstring,
            # For now, we only have one version of the model, so we can use 0
            module=model_entity.model.module_path
        ) for model_entity in self.input_model_entities]

        swe_runner = SWEAgentRunner(
            user_id=self.user_id,
            bearer_token=self.bearer_token,
            conversation_id=self.conversation_id,
            parent_run_id=self.run_id,
            structure_ids_to_inject=structure_ids_to_inject,
            inject_synthetic_data_descriptions=True,
            functions_to_inject=functions_to_inject,
            models_to_inject=models_to_inject,
            log=True
        )

        try:
            test_code = create_test_code_from_spec(
                self.bearer_token,
                pipeline_spec_run.output,
                self.input_model_entities
            )

            swe_prompt = (
                "I have been tasked to compose a data processing pipeline. For context, this is my full task description:\n\n" +
                f"'{PIPELINE_AGENT_SYSTEM_PROMPT}'\n\n" +
                f"Now I need you to implement the final pipeline. This is the spec :\n\n{pipeline_spec_run.output.model_dump_json()}\n\n" +
                "Use these functions. In case new ones are needed to build the pipeline, implement them. " +
                "Define new files for the new functions. The main pipeline function should just wire together the inputs and outputs of the functions, not define new logic. " +
                "Use the pipeline name in the spec to name the pipeline function. "
                "Go!"
            )

            implementation_approved = False
            self.tries = 0

            await self._log_message("Implementing pipeline", "tool_call", write_to_db=True)

            while not implementation_approved:
                if self.tries >= SWE_MAX_TRIES:
                    raise RuntimeError(
                        f"SWE agent failed to implement pipeline after {SWE_MAX_TRIES} tries")

                self.tries += 1
                swe_output = await swe_runner(swe_prompt, test_code)

                feedback_prompt = (
                    "The software engineer agent has submitted a solution.\n" +
                    f"Its result is:\n\n{swe_output.model_dump_json()}\n\n" +
                    "Decide whether to accept it, or reject it with feedback on what to fix before the solution is approved."
                )

                feedback_run = await self._run_agent(
                    feedback_prompt,
                    output_type=ImplementationFeedbackOutput,
                    deps=PipelineAgentDeps(client=self.project_client)
                )

                implementation_approved = feedback_run.output.approved
                swe_prompt = feedback_run.output.feedback

                await self._log_message(f"Implementation approved: {implementation_approved}", "result", write_to_db=True)
                await self._log_message(f"Feedback: {swe_prompt}", "result", write_to_db=True)

                if implementation_approved:
                    swe_runner.delete_temporary_scripts()
                    swe_output = swe_runner.get_final_output()
                    return pipeline_spec_run.output, swe_output

        except Exception as e:
            swe_runner.delete_temporary_scripts()
            raise e

    async def _run_pipeline_implementation_summary_stage(
        self
    ) -> Tuple[List[FunctionImplementationSpec], List[FunctionUpdateCreate], List[ModelUpdateCreate], PipelineGraphOutput, PipelineImplementationSpec]:
        # Outputs the implementation summary

        new_functions_run = await self._run_agent(
            "Now that the pipeline script has been approved, output information about which new functions have been created. " +
            "If no new functions have been created, output an empty list. The main function in the pipeline script should not be included here. " +
            "Go!",
            output_type=List[FunctionImplementationSpec],
            deps=PipelineAgentDeps(client=self.project_client)
        )

        await self._log_message(
            f"New functions: {new_functions_run.output}", "result", write_to_db=True)

        updates_run = await self._run_agent(
            "Now that the pipeline script has been approved, output information about which of the existing functions have been modified. " +
            "If no functions have been modified, output an empty list. " +
            "NB: The definition_id points to the id of the function definition (not the function id). " +
            "Go!",
            output_type=List[FunctionUpdateOutput],
            deps=PipelineAgentDeps(client=self.project_client)
        )

        await self._log_message(
            f"Function updates: {updates_run.output}", "result", write_to_db=True)

        model_updates_run = await self._run_agent(
            "Now that the pipeline script has been approved, output information about which of the existing models have been modified. " +
            "If no models have been modified, output an empty list. " +
            "NB: The definition_id points to the id of the model definition (not the model id). " +
            "Go!",
            output_type=List[ModelUpdateOutput],
            deps=PipelineAgentDeps(client=self.project_client)
        )

        await self._log_message(
            f"Model updates: {model_updates_run.output}", "result", write_to_db=True)

        graph_run = await self._run_agent(
            "Now, based on the code, output information about the computational graph of the pipeline. Go!",
            output_type=PipelineGraphOutput,
            deps=PipelineAgentDeps(client=self.project_client)
        )

        await self._log_message(
            f"Pipeline graph: {graph_run.output}", "result", write_to_db=True)

        final_spec_run = await self._run_agent(
            "Now that you've documented the implementation, provide the final pipeline specification that reflects any changes made during implementation. This is the authoritative spec for what was actually built. Go!",
            output_type=PipelineImplementationSpec,
            deps=PipelineAgentDeps(client=self.project_client)
        )

        return new_functions_run.output, updates_run.output, model_updates_run.output, graph_run.output, final_spec_run.output

    def _get_new_functions_create(
        self,
        new_functions: List[FunctionImplementationSpec],
        swe_output: SWEAgentOutput
    ) -> List[FunctionCreate]:

        new_functions_create = []

        for fn_desc in new_functions:
            script = next(
                (res.script for res in swe_output.implementation.new_scripts if res.filename == fn_desc.filename), None)

            assert script is not None, f"Agent outputted a new script but no script for function {fn_desc.filename} found"

            implementation_storage = file_manager.save_script(
                fn_desc.filename,
                script,
                "function"
            )

            new_function = FunctionCreate(
                **fn_desc.model_dump(),
                implementation_script_path=str(
                    implementation_storage.script_path),
                module_path=implementation_storage.module_path
            )

            new_function.filename = Path(
                implementation_storage.script_path).name

            new_functions_create.append(new_function)

        return new_functions_create

    def _get_function_updates_create(
        self,
        function_updates: List[FunctionUpdateOutput],
        functions_used: List[FunctionFull],
        swe_output: SWEAgentOutput
    ) -> List[FunctionUpdateCreate]:

        functions_updated = []

        for fn in functions_used:
            update = next(
                (u for u in function_updates if u.definition_id == fn.definition.id), None)
            if update is not None:
                new_script, new_filename = next(
                    ((res.new_script, res.new_filename)
                     for res in swe_output.implementation.modified_scripts if res.original_filename == fn.filename), (None, None))

                assert new_script is not None, f"Agent outputted a modification but no new script for function {fn.filename} found"

                implementation_storage = file_manager.save_script(
                    new_filename,
                    new_script,
                    "function"
                )

                functions_updated.append(FunctionUpdateCreate(
                    **update.model_dump(),
                    updated_implementation_script_path=str(
                        implementation_storage.script_path),
                    updated_module_path=implementation_storage.module_path,
                    updated_filename=Path(
                        implementation_storage.script_path).name,
                ))

        return functions_updated

    def _get_model_updates_create(
        self,
        model_updates: List[ModelUpdateOutput],
        models_used: List[ModelEntityWithModelDef],
        swe_output: SWEAgentOutput
    ) -> List[ModelUpdateCreate]:

        models_updated = []

        for model_entity in models_used:
            update = next(
                (u for u in model_updates if u.definition_id == model_entity.model.definition.id), None)
            if update is not None:
                new_script, new_filename = next(
                    ((res.new_script, res.new_filename)
                     for res in swe_output.implementation.modified_scripts if res.original_filename == model_entity.model.filename), (None, None))

                assert new_script is not None, f"Agent outputted a modification but no new script for model {model_entity.model.filename} found"

                implementation_storage = file_manager.save_script(
                    new_filename,
                    new_script,
                    "model"
                )

                models_updated.append(ModelUpdateCreate(
                    **update.model_dump(),
                    updated_implementation_script_path=str(
                        implementation_storage.script_path),
                    updated_module_path=implementation_storage.module_path,
                    updated_filename=Path(
                        implementation_storage.script_path).name,
                    model_entities_to_update=[model_entity.id]
                ))
        return models_updated

    def _graph_output_to_graph_create(
        self,
        pipeline_graph: PipelineGraphOutput,
        functions_used: List[FunctionFull]
    ) -> PipelineGraphCreate:

        pipeline_nodes_create = []
        for node in pipeline_graph.nodes:
            from_dataset_ids = [
                next(d for d in self.input_datasets if d.name == dataset_name).id for dataset_name in node.from_datasets
            ]
            from_function_ids = [
                next(f for f in functions_used if f.python_function_name == function_name).id for function_name in node.from_functions
            ]
            from_model_entity_ids = [
                next(m for m in self.input_model_entities if m.name == model_entity_name).id for model_entity_name in node.from_model_entities
            ]
            if node.type == "function":
                fn_id = next(
                    f for f in functions_used if f.definition.name == node.name).id
                pipeline_nodes_create.append(PipelineNodeCreate(
                    entity_id=fn_id,
                    type="function",
                    from_dataset_ids=from_dataset_ids,
                    from_function_ids=from_function_ids,
                    from_model_entity_ids=from_model_entity_ids
                ))
            elif node.type == "model_entity":
                model_entity_id = next(
                    m for m in self.input_model_entities if m.name == node.name).id
                pipeline_nodes_create.append(PipelineNodeCreate(
                    entity_id=model_entity_id,
                    type="model_entity",
                    model_function_type=node.model_function_type,
                    from_dataset_ids=from_dataset_ids,
                    from_function_ids=from_function_ids,
                    from_model_entity_ids=from_model_entity_ids
                ))
            elif node.type == "dataset":
                dataset_id = next(
                    d for d in self.input_datasets if d.name == node.name).id
                pipeline_nodes_create.append(PipelineNodeCreate(
                    entity_id=dataset_id,
                    type="dataset",
                    from_dataset_ids=from_dataset_ids,
                    from_function_ids=from_function_ids,
                    from_model_entity_ids=from_model_entity_ids
                ))
            else:
                raise ValueError(f"Invalid node type: {node.type}")

        return PipelineGraphCreate(nodes=pipeline_nodes_create)

    async def _save_results(
        self,
        existing_functions: List[FunctionFull],
        new_functions: List[FunctionImplementationSpec],
        final_pipeline_spec: PipelineImplementationSpec,
        pipeline_implementation: SWEAgentOutput,
        function_updates: List[FunctionUpdateOutput],
        model_updates: List[ModelUpdateOutput],
        pipeline_graph: PipelineGraphOutput
    ) -> PipelineInDB:
        # TODO: Add validation to ensure the new scripts don't already exist

        new_function_creates = self._get_new_functions_create(
            new_functions, pipeline_implementation)

        new_functions = []
        for function_create in new_function_creates:
            new_function = await post_function(self.project_client, function_create)
            new_functions.append(FunctionFull(**new_function.model_dump()))

        function_update_creates = self._get_function_updates_create(
            function_updates, existing_functions + new_functions, pipeline_implementation)

        for function_update in function_update_creates:
            await post_update_function(self.project_client, function_update)

        model_update_creates = self._get_model_updates_create(
            model_updates, self.input_model_entities, pipeline_implementation)

        for model_update in model_update_creates:
            await post_update_model(self.project_client, model_update)

        final_script = create_final_pipeline_script(
            pipeline_implementation.implementation.main_script, final_pipeline_spec, self.input_model_entities)
        pipeline_script = file_manager.save_script(
            f"{final_pipeline_spec.python_function_name}.py", final_script, "pipeline", add_uuid=True, temporary=False)

        # computational_graph = self._graph_output_to_graph_create(
        #     pipeline_graph, existing_functions + new_functions)

        # TODO: Implement this
        computational_graph = PipelineGraphCreate(nodes=[])

        pipeline_create = PipelineCreate(
            **final_pipeline_spec.model_dump(),
            implementation_script_path=str(pipeline_script.script_path),
            filename=Path(pipeline_script.script_path).name,
            module_path=pipeline_script.module_path,
            function_ids=[f.id for f in existing_functions + new_functions],
            computational_graph=computational_graph
        )

        pipeline_response = await post_pipeline(self.project_client, pipeline_create)

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

        return pipeline_response


@broker.task(retry_on_error=False)
async def run_pipeline_agent_task(
        user_id: uuid.UUID,
        project_id: uuid.UUID,
        conversation_id: uuid.UUID,
        run_id: uuid.UUID,
        prompt_content: str,
        bearer_token: str,
        input_dataset_ids: List[uuid.UUID],
        input_model_entity_ids: List[uuid.UUID] = []
):

    runner = PipelineAgentRunner(
        user_id=user_id,
        project_id=project_id,
        conversation_id=conversation_id,
        run_id=run_id,
        bearer_token=bearer_token,
        input_dataset_ids=input_dataset_ids,
        input_model_entity_ids=input_model_entity_ids,
    )

    await runner(prompt_content)
