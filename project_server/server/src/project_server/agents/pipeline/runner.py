import uuid
from pathlib import Path
from typing import Optional, List

from project_server.entity_manager import file_manager
from project_server.agents.pipeline.agent import pipeline_agent
from project_server.agents.pipeline.prompt import PIPELINE_AGENT_SYSTEM_PROMPT
from project_server.agents.pipeline.output import (
    FunctionToImplementOutput,
    FunctionsInPipelineOutput,
    FunctionsInPipelineWithPopulatedFunctions,
    DetailedFunctionDescription,
    ImplementationFeedbackOutput,
    DetailedPipelineDescription,
    submit_detailed_function_description_output,
    submit_final_pipeline_output,
    PipelineAgentFinalOutput,
    FunctionInPipelineOutput
)
from project_server.agents.swe.runner import SWEAgentRunner, SWEAgentOutput
from project_server.agents.swe.deps import ScriptToInject
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
    post_update_function
)
from project_server.agents.pipeline.utils import create_test_code_from_fn_spec
from project_server.agents.runner_base import RunnerBase
from project_server.agents.pipeline.sandbox_code import create_final_pipeline_script

from synesis_schemas.main_server import (
    PipelineCreate,
    FunctionCreate,
    AddEntityToProject,
    FrontendNodeCreate,
    SearchFunctionsRequest,
    QueryRequest,
    GetDatasetByIDsRequest,
    GetModelEntityByIDsRequest,
    FunctionBare,
    FunctionUpdateCreate,
    FunctionInPipelineCreate,
    InputVariableMappingCreate,
    DatasetFullWithFeatures,
    ModelEntityFull
)


class PipelineAgentRunner(RunnerBase):

    def __init__(
            self,
            user_id: str,
            project_id: uuid.UUID,
            conversation_id: uuid.UUID,
            bearer_token: str,
            input_dataset_ids: List[uuid.UUID],
            input_model_entity_ids: List[uuid.UUID] = [],
            run_id: Optional[uuid.UUID] = None):

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

        self.input_datasets: List[DatasetFullWithFeatures] = []
        self.input_model_entities: List[ModelEntityFull] = []

    async def __call__(self, prompt_content: str) -> PipelineCreate:

        try:
            await self._create_run_if_not_exists()

            search_stage_output = await self._run_search_stage(prompt_content)

            new_functions = await self._run_function_implementation_stage(search_stage_output.functions_to_implement)
            all_functions = search_stage_output.existing_functions + new_functions
            final_pipeline_output = await self._run_pipeline_implementation_stage(all_functions)

            await self._save_results(final_pipeline_output, all_functions)
            await self._complete_agent_run("Pipeline agent run completed")

            return final_pipeline_output

        except Exception as e:
            await self._fail_agent_run(f"Error running pipeline agent: {e}")
            raise e

    async def _run_search_stage(self, prompt_content: str) -> FunctionsInPipelineWithPopulatedFunctions:
        # Searches for existing functions, outputs the results

        self.input_datasets = await get_datasets_by_ids(self.project_client, GetDatasetByIDsRequest(dataset_ids=self.input_dataset_ids, include_features=True))
        self.input_model_entities = await get_model_entities_by_ids(self.project_client, GetModelEntityByIDsRequest(model_entity_ids=self.input_model_entity_ids))

        search_run = await self._run_agent(
            f"The user has requested a pipeline with the following description: {prompt_content}\n\n" +
            f"The input datasets are:\n\n{[ds.model_dump_json() for ds in self.input_datasets]}\n\n" +
            f"The input model entities are:\n\n{[me.model_dump_json() for me in self.input_model_entities]}\n\n" +
            "Now search for any relevant functions! If the model functions suffice, you can output an empty list.",
            output_type=List[QueryRequest]
        )

        if len(search_run.output):
            await self._log_message("Searching knowledge bank", "result", write_to_db=True)

            search_response = await post_search_functions(self.project_client, SearchFunctionsRequest(
                queries=search_run.output
            ))

            await self._log_message(f"Function search results: {search_response}", "result", write_to_db=True)
        else:
            search_response = []

        pipeline_run = await self._run_agent(
            f"The search results are:\n\n{search_response}\n\n" +
            "Now determine whether these suffice to compose the final pipeline, or if new functions must be implemented. " +
            "In case we need new ones, submit descriptions for each." +
            "Output information about the pipeline, implementation instructions, existing functions to use, and / or new functions to implement.",
            output_type=FunctionsInPipelineOutput
        )

        existing_functions = []
        for fn_name in pipeline_run.output.existing_functions_to_use_names:
            existing_function = next(
                fn for query_result in search_response for fn in query_result.functions if fn.name == fn_name
            )

            if not existing_function:
                raise RuntimeError(
                    f"Agent selected function '{fn_name}' that does not exist in the search results.")

            existing_functions.append(existing_function)

        return FunctionsInPipelineWithPopulatedFunctions(
            **pipeline_run.output.model_dump(),
            existing_functions=existing_functions
        )

    async def _run_function_implementation_stage(self, functions_to_implement: List[FunctionToImplementOutput]) -> List[FunctionBare]:
        # Sequentially implements each function, outputs the results

        if len(functions_to_implement) == 0:
            return []

        await self._log_message("Implementing functions", "result", write_to_db=True)
        new_functions: List[FunctionBare] = []

        for fn_desc in functions_to_implement:
            fn_spec_run = await self._run_agent(
                f"We are currently looking at the function '{fn_desc.name}'\n" +
                f"A brief description of the function is:\n\n{fn_desc.brief_description}\n\n" +
                "Please create a detailed implementation spec for the software engineer agent.\n",
                output_type=submit_detailed_function_description_output
            )

            fn_spec_output: DetailedFunctionDescription = fn_spec_run.output

            input_structure_ids = [
                input.structure_id for input in fn_spec_output.input_object_groups
            ]

            output_structure_ids = [
                output.structure_id for output in fn_spec_output.output_object_groups
            ]

            deliverable_description = (
                "I have been tasked to compose a data processing pipeline. For context, this is my full task description:\n\n" +
                f"'{PIPELINE_AGENT_SYSTEM_PROMPT}'\n\n" +
                f"Now I need you to implement a function as part of the pipeline. You need to implement:\n\n{fn_spec_output.model_dump_json()}\n\n" +
                "Give the function the name specified in the spec!"
                "Go!"
            )

            test_code = create_test_code_from_fn_spec(fn_spec_output)

            swe_prompt = deliverable_description

            await self._log_message("Calling SWE agent to implement function", "tool_call", write_to_db=True)

            swe_runner = SWEAgentRunner(
                self.user_id,
                self.bearer_token,
                self.conversation_id,
                self.run_id,
                structure_ids_to_inject=input_structure_ids+output_structure_ids,
                inject_synthetic_data_descriptions=True,
                log=True
            )

            implementation_approved = False
            self.tries = 0

            while not implementation_approved:

                if self.tries >= SWE_MAX_TRIES:
                    raise RuntimeError(
                        f"SWE agent failed to implement function {fn_desc.name} after {SWE_MAX_TRIES} tries")

                self.tries += 1

                swe_result = await swe_runner(swe_prompt, test_code)

                feedback_prompt = (
                    "The software engineer agent has submitted a solution.\n" +
                    f"Its result is:\n\n{swe_result.model_dump_json()}\n\n" +
                    "Decide whether to accept it, or reject it with feedback on what to fix before the solution is approved."
                )

                await self._log_message(f"Feedback prompt: {feedback_prompt}", "result", write_to_db=True)

                feedback_run = await self._run_agent(
                    feedback_prompt,
                    output_type=ImplementationFeedbackOutput
                )

                implementation_approved = feedback_run.output.approved
                swe_prompt = feedback_run.output.feedback

                await self._log_message(f"Implementation approved: {implementation_approved}", "result", write_to_db=True)
                await self._log_message(f"Feedback: {swe_prompt}", "result", write_to_db=True)

                if implementation_approved:

                    await self._log_message("Implementation approved, saving function", "result", write_to_db=True)

                    implementation_script_path = file_manager.save_function_script(
                        fn_desc.name,
                        swe_result.implementation.script,
                        0,
                        is_temporary=False
                    )

                    if swe_result.setup:
                        setup_script_path = file_manager.save_function_script(
                            fn_desc.name,
                            swe_result.setup.script,
                            0,
                            is_temporary=False,
                            is_setup=True
                        )
                    else:
                        setup_script_path = None

                    new_function = await post_function(self.project_client, FunctionCreate(
                        name=fn_desc.name,
                        description=fn_spec_output.description,
                        implementation_script_path=str(
                            implementation_script_path),
                        setup_script_path=str(
                            setup_script_path) if setup_script_path else None,
                        default_args_dict=swe_result.config.config_dict if swe_result.config else None,
                        args_dataclass_name=fn_spec_output.args_dataclass_name,
                        input_dataclass_name=fn_spec_output.input_dataclass_name,
                        output_dataclass_name=fn_spec_output.output_dataclass_name,
                        output_variables_dataclass_name=fn_spec_output.output_variables_dataclass_name,
                        type=fn_spec_output.type,
                        input_object_group_descriptions=[inp.model_dump()
                                                         for inp in fn_spec_output.input_object_groups],
                        output_object_group_descriptions=[out.model_dump()
                                                          for out in fn_spec_output.output_object_groups],
                        output_variables_descriptions=[out.model_dump()
                                                       for out in fn_spec_output.output_variables]
                    ))

                    new_functions.append(new_function)

                else:
                    await self._log_message(
                        f"Implementation rejected. Feedback: {swe_prompt}", "result", write_to_db=True)

        await self._log_message("All new functions implemented", "result", write_to_db=True)

        return new_functions

    async def _run_pipeline_implementation_stage(
        self,
        functions_to_use: List[FunctionBare]
    ) -> PipelineAgentFinalOutput:
        # Composes the full pipeline script, evaluates the results, modifies the functions if necessary, saves the pipeline and updated functions

        pipeline_spec_run = await self._run_agent(
            "Now that we have all needed functions, it is time to compose the final pipeline. " +
            "We will dispatch the software engineer agent to implement the pipeline. " +
            "Now provide a detailed implementation spec for the software engineer agent.",
            output_type=DetailedPipelineDescription
        )

        def _extract_structure_ids_from_functions(functions: List[FunctionBare]) -> List[str]:
            return list(set([
                input.structure_id for function in functions for input in function.input_object_groups
            ] + [
                output.structure_id for function in functions for output in function.output_object_groups
            ]))

        def _extract_scripts_to_inject(functions: List[FunctionBare]) -> List[ScriptToInject]:
            return [ScriptToInject(
                script_name=function.name,
                script_path=function.implementation_script_path
            ) for function in functions]

        structure_ids_to_inject = _extract_structure_ids_from_functions(
            functions_to_use)

        scripts_to_inject = _extract_scripts_to_inject(functions_to_use)

        swe_runner = SWEAgentRunner(
            user_id=self.user_id,
            bearer_token=self.bearer_token,
            conversation_id=self.conversation_id,
            parent_run_id=self.run_id,
            structure_ids_to_inject=structure_ids_to_inject,
            inject_synthetic_data_descriptions=True,
            scripts_to_inject=scripts_to_inject,
            log=True
        )

        test_code = create_test_code_from_fn_spec(pipeline_spec_run.output)

        swe_prompt = (
            "I have been tasked to compose a data processing pipeline. For context, this is my full task description:\n\n" +
            f"'{PIPELINE_AGENT_SYSTEM_PROMPT}'\n\n" +
            f"Now I need you to implement the final pipeline, using the prebuilt functions made available to you. This is the spec (ignore the schedules):\n\n{pipeline_spec_run.output.model_dump_json()}\n\n" +
            "Use the pipeline name in the spec to name the pipeline function. "
            "Go!"
        )

        implementation_approved = False
        self.tries = 0
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
                output_type=ImplementationFeedbackOutput
            )

            implementation_approved = feedback_run.output.approved
            swe_prompt = feedback_run.output.feedback

            await self._log_message(f"Implementation approved: {implementation_approved}", "result", write_to_db=True)
            await self._log_message(f"Feedback: {swe_prompt}", "result", write_to_db=True)

            if implementation_approved:
                describe_functions_run = await self._run_agent(
                    "Now that the pipeline script has been approved, output the details about the functions used and their input/output variables, " +
                    "and details about modifications done by the SWE agent to the functions. " +
                    "Go!",
                    output_type=submit_final_pipeline_output
                )
                swe_runner.delete_temporary_scripts()

                return PipelineAgentFinalOutput(
                    **pipeline_spec_run.output.model_dump(),
                    functions=describe_functions_run.output,
                    swe_output=swe_output
                )

    async def _save_results(
        self,
        pipeline_output: PipelineAgentFinalOutput,
        functions_used: List[FunctionBare]
    ) -> None:
        """
        Need to go from agent out to pipeline create by mapping IDs, 
        then create updated FunctionCreate, and FunctionUpdateCreate, replacing "functions_tmp" with "functions" in all the scripts, then writing these scripts to file.
        Finally, create the final pipeline script (again replacing "functions_tmp" with "functions" in the scripts), add code to load the datasets and model entities, 
        and save the the output object groups and variables, 
        then save the pipeline and create the output dataset and model entity. 
        """

        # TODO: Add validation to ensure the new scripts don't already exist

        def _get_function_updates(
            pipeline_functions: List[FunctionInPipelineOutput],
            functions_used: List[FunctionBare],
            swe_output: SWEAgentOutput
        ) -> List[FunctionUpdateCreate]:

            modified_functions = [
                f for f in pipeline_functions if f.function_modified is not None]
            functions_updated = []

            for fn in functions_used:
                modification = next(
                    (f.function_modified for f in modified_functions if f.function_name == fn.name), None)
                if modification is not None:

                    new_script = next(
                        [res.new_script for res in swe_output.implementation.modified_scripts if res.script_name == fn.name], None)

                    assert new_script is not None, f"Agent outputted a modification but no new script for function {fn.name} found"

                    implementation_script_path = file_manager.save_function_script(
                        fn.name, new_script, fn.version+1, is_temporary=False)

                    input_object_groups_to_remove_ids = [
                        g.id for g in fn.input_object_groups if g.name in modification.input_object_group_variables_removed]
                    output_object_groups_to_remove_ids = [
                        g.id for g in fn.output_object_groups if g.name in modification.output_object_group_variables_removed]
                    output_variables_to_remove_ids = [
                        g.id for g in fn.output_variables if g.name in modification.output_variable_group_variables_removed]

                    functions_updated.append(FunctionUpdateCreate(
                        definition_id=fn.definition_id,
                        implementation_script_path=implementation_script_path,
                        # TODO: Add support for updating the setup script path
                        # setup_script_path=setup_script_path,
                        input_object_group_descriptions_to_remove=input_object_groups_to_remove_ids,
                        output_object_group_descriptions_to_remove=output_object_groups_to_remove_ids,
                        output_variables_descriptions_to_remove=output_variables_to_remove_ids,
                        **modification.model_dump()
                    ))

            return functions_updated

        def _save_final_pipeline_script(pipeline_spec: PipelineAgentFinalOutput) -> Path:
            """
            - Add code to load the datasets and model entities
            - Add code to save the output object groups and variables
            - Save the script
            - Return the path to the script
            """

            final_script = create_final_pipeline_script(
                pipeline_spec,
                pipeline_spec.swe_output.implementation.script,
                self.input_dataset_ids
            )

            return file_manager.save_pipeline_script(pipeline_spec.name, final_script)

        def _pipeline_agent_output_to_pipeline_create(
            pipeline_agent_output: PipelineAgentFinalOutput,
            functions_used: List[FunctionBare],
            pipeline_script_path: Path
        ) -> PipelineCreate:
            # TODO: Implement

            functions_in_pipeline_create = []

            for pipe_fn in pipeline_agent_output.functions:
                fn = next(f for f in functions_used if f.name ==
                          pipe_fn.function_name)
                mappings = [
                    InputVariableMappingCreate(
                        to_function_input_object_group_id=next(
                            g.id for g in fn.input_object_groups if g.name == mapping.to_function_input_object_group_variable),
                        from_function_output_object_group_id=next((
                            g.id for f in functions_used for g in f.output_object_groups
                            if mapping.from_function_output_object_group_variable and f.name == mapping.from_function_output_object_group_variable.source_function_name
                            and g.name == mapping.from_function_output_object_group_variable.source_object_group_variable), None),
                        from_dataset_object_group_id=next((
                            g.id for ds in self.input_datasets for g in ds.object_groups
                            if mapping.from_dataset_object_group_variable and g.name == mapping.from_dataset_object_group_variable.source_object_group_variable
                            and ds.name == mapping.from_dataset_object_group_variable.source_dataset_name
                        ), None),
                    ) for mapping in pipe_fn.input_variable_mappings
                ]
                output_object_groups_to_save_ids = [
                    g.id for g in fn.output_object_groups if g.name in pipe_fn.output_object_group_variables_to_save
                ]
                output_variable_groups_to_save_ids = [
                    g.id for g in fn.output_variables if g.name in pipe_fn.output_variable_group_variables_to_save
                ]

                functions_in_pipeline_create.append(FunctionInPipelineCreate(
                    function_id=fn.id,
                    input_variable_mappings=mappings,
                    output_object_groups_to_save_ids=output_object_groups_to_save_ids,
                    output_variable_groups_to_save_ids=output_variable_groups_to_save_ids
                ))

            pipeline_create = PipelineCreate(
                name=pipeline_agent_output.name,
                description=pipeline_agent_output.description,
                implementation_script_path=str(pipeline_script_path),
                args_dataclass_name=pipeline_agent_output.args_dataclass_name,
                input_dataclass_name=pipeline_agent_output.input_dataclass_name,
                output_dataclass_name=pipeline_agent_output.output_dataclass_name,
                output_variables_dataclass_name=pipeline_agent_output.output_variables_dataclass_name,
                args_dict=pipeline_agent_output.args_dict,
                functions=functions_in_pipeline_create,
                input_dataset_ids=self.input_dataset_ids,
                input_model_entity_ids=self.input_model_entity_ids,
                periodic_schedules=pipeline_agent_output.periodic_schedules,
                on_event_schedules=pipeline_agent_output.on_event_schedules
            )

            return pipeline_create

        function_updates = _get_function_updates(
            pipeline_output.functions, functions_used, pipeline_output.swe_output)

        for function_update in function_updates:
            await post_update_function(self.project_client, function_update)

        pipeline_script_path = _save_final_pipeline_script(pipeline_output)

        pipeline_create = _pipeline_agent_output_to_pipeline_create(
            pipeline_output,
            functions_used,
            pipeline_script_path
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


@broker.task(retry_on_error=False)
async def run_pipeline_task(
        user_id: uuid.UUID,
        project_id: uuid.UUID,
        conversation_id: uuid.UUID,
        prompt_content: str,
        bearer_token: str,
        input_dataset_ids: List[uuid.UUID],
        input_model_entity_ids: List[uuid.UUID] = []
):

    runner = PipelineAgentRunner(
        user_id=user_id,
        project_id=project_id,
        conversation_id=conversation_id,
        bearer_token=bearer_token,
        input_dataset_ids=input_dataset_ids,
        input_model_entity_ids=input_model_entity_ids
    )

    await runner(prompt_content)
