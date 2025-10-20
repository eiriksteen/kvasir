import uuid
import shutil
from typing import List, Optional
from pydantic import BaseModel
from pydantic_ai import RunContext, ModelRetry
from pathlib import Path

from synesis_data_interface.structures.overview import get_first_level_structure_ids
from project_server.agents.swe.deps import SWEAgentDeps
from project_server.utils.code_utils import run_python_code_in_container
from project_server.agents.runner_base import CodeForLog
from project_server.client import submit_swe_result_approval_request
from project_server.worker import logger
from project_server.agents.swe.sandbox_code import add_object_group_validation_code_to_implementation, add_entry_point
from synesis_schemas.main_server import (
    FunctionInputObjectGroupDefinitionCreate,
    FunctionOutputObjectGroupDefinitionCreate,
    ModelFunctionInputObjectGroupDefinitionCreate,
    ModelFunctionOutputObjectGroupDefinitionCreate,
    SUPPORTED_MODALITIES_TYPE,
    SUPPORTED_TASK_TYPE,
    ModelFunctionCreate,
    Implementation,
    NewScript,
    ModifiedScript,
    Function,
    ModelSourceCreate
)
from project_server.app_secrets import MODEL_WEIGHTS_DIR


class FunctionImplementationSummary(BaseModel):
    name: str
    python_function_name: str
    filename: str
    docstring: str
    description: str
    args_schema: dict
    default_args: dict
    output_variables_schema: dict
    input_object_groups: List[FunctionInputObjectGroupDefinitionCreate]
    output_object_group_definitions: List[FunctionOutputObjectGroupDefinitionCreate]
    setup_script_path: Optional[str] = None


class ModelImplementationSummary(BaseModel):
    name: str
    python_class_name: str
    filename: str
    description: str
    modality: SUPPORTED_MODALITIES_TYPE
    task: SUPPORTED_TASK_TYPE
    model_class_docstring: str
    training_function: ModelFunctionCreate
    inference_function: ModelFunctionCreate
    source: ModelSourceCreate
    default_config: dict
    config_schema: dict


class FunctionUpdateOutput(BaseModel):
    definition_id: uuid.UUID
    updates_made_description: str
    updated_python_function_name: Optional[str] = None
    updated_description: Optional[str] = None
    updated_docstring: Optional[str] = None
    updated_setup_script_path: Optional[str] = None
    updated_default_args: Optional[dict] = None
    updated_args_schema: Optional[dict] = None
    updated_output_variables_schema: Optional[dict] = None
    input_object_groups_to_add: Optional[
        List[FunctionInputObjectGroupDefinitionCreate]] = None
    output_object_group_definitions_to_add: Optional[
        List[FunctionOutputObjectGroupDefinitionCreate]] = None
    input_object_groups_to_remove: Optional[List[uuid.UUID]] = None
    output_object_group_definitions_to_remove: Optional[List[uuid.UUID]] = None


class ModelUpdateOutput(BaseModel):
    definition_id: uuid.UUID
    updates_made_description: str
    updated_python_class_name: Optional[str] = None
    updated_description: Optional[str] = None
    updated_docstring: Optional[str] = None
    updated_setup_script_path: Optional[str] = None
    updated_default_args: Optional[dict] = None
    updated_args_schema: Optional[dict] = None
    updated_output_variables_schema: Optional[dict] = None
    input_object_groups_to_add: Optional[
        List[ModelFunctionInputObjectGroupDefinitionCreate]] = None
    output_object_group_definitions_to_add: Optional[
        List[ModelFunctionOutputObjectGroupDefinitionCreate]] = None
    input_object_groups_to_remove: Optional[List[uuid.UUID]] = None
    output_object_group_definitions_to_remove: Optional[List[uuid.UUID]] = None


class ImplementationSummaryOutput(BaseModel):
    # pipeline_output_variable_name: str
    new_main_function: FunctionImplementationSummary
    new_supporting_functions: List[FunctionImplementationSummary]
    new_models: List[ModelImplementationSummary]
    modified_functions: List[FunctionUpdateOutput]
    modified_models: List[ModelUpdateOutput]


class ImplementationSummaryOutputWithImplementation(ImplementationSummaryOutput):
    implementation: Implementation
    functions_used: List[Function]


async def submit_implementation_output(ctx: RunContext[SWEAgentDeps], file_name: str, result: ImplementationSummaryOutput) -> ImplementationSummaryOutputWithImplementation:

    testing_args = {**result.new_main_function.default_args}
    testing_dirs: List[Path] = []

    for new_model in result.new_models:
        if f"{new_model.python_class_name}_config" not in result.new_main_function.default_args:
            raise ModelRetry(
                f"The config for the new model {new_model.python_class_name} must be included in the default args and must be named {new_model.python_class_name}_config")

        # testing_dir = MODEL_WEIGHTS_DIR / f"{uuid.uuid4()}"
        # testing_dir.mkdir(parents=True, exist_ok=True)
        # testing_args[f"{new_model.python_class_name}_config"]["weights_save_dir"] = testing_dir
        # testing_dirs.append(testing_dir)

    for injected_model in ctx.deps.model_entities_injected:
        if f"{injected_model.implementation.model_implementation.python_class_name}_config" not in result.new_main_function.default_args:
            raise ModelRetry(
                f"The config for the injected model {injected_model.implementation.model_implementation.python_class_name} must be included in the default args and must be named {injected_model.implementation.model_implementation.python_class_name}_config")

        # testing_dir = MODEL_WEIGHTS_DIR / f"{uuid.uuid4()}"
        # testing_dir.mkdir(parents=True, exist_ok=True)
        # testing_args[f"{injected_model.implementation.model_implementation.python_class_name}_config"]["weights_save_dir"] = testing_dir
        # testing_dirs.append(testing_dir)

    for function in result.new_supporting_functions:
        if f"{function.python_function_name}_config" not in result.new_main_function.default_args:
            raise ModelRetry(
                f"The config for the new function {function.python_function_name} must be included in the default args and must be named {function.python_function_name}_args")

    for loaded_function in ctx.deps.functions_loaded:
        if f"{loaded_function.implementation_script.filename}_args" not in result.new_main_function.default_args:
            raise ModelRetry(
                f"The config for the loaded function {loaded_function.implementation_script.filename} must be included in the default args and must be named {loaded_function.implementation_script.filename}_args")

    first_level_structure_ids = get_first_level_structure_ids()

    for function in [result.new_main_function, *result.new_supporting_functions]:
        for input in function.input_object_groups:
            if input.structure_id not in first_level_structure_ids:
                raise ModelRetry(
                    f"Invalid structure ID: {input.structure_id}, available structures: {first_level_structure_ids}")

        for output in function.output_object_group_definitions:
            if output.structure_id not in first_level_structure_ids:
                raise ModelRetry(
                    f"Invalid structure ID: {output.structure_id}, available structures: {first_level_structure_ids}")

    for model in result.new_models:
        for object_group in [model.training_function.input_object_groups, model.inference_function.input_object_groups]:
            for input in object_group:
                if input.structure_id not in first_level_structure_ids:
                    raise ModelRetry(
                        f"Invalid structure ID: {input.structure_id}, available structures: {first_level_structure_ids}")

        for object_group in [model.training_function.output_object_groups, model.inference_function.output_object_groups]:
            for output in object_group:
                if output.structure_id not in first_level_structure_ids:
                    raise ModelRetry(
                        f"Invalid structure ID: {output.structure_id}, available structures: {first_level_structure_ids}")

    if file_name not in ctx.deps.current_scripts:
        raise ModelRetry(
            f"Script {file_name} does not exist. The available scripts are: {list(ctx.deps.current_scripts.keys())}. To create a new script, call the write_script tool.")

    script = ctx.deps.current_scripts[file_name]

    if "outputs" not in script:
        raise ModelRetry(
            f"The pipeline output variable name 'outputs' was not found in the script. The pipeline output variable in the main loop must have this name. ")

    script = add_object_group_validation_code_to_implementation(
        script, result.new_main_function.output_object_group_definitions)

    script_to_run = add_entry_point(
        script, ctx.deps.bearer_token, testing_args)

    logger.info("CURRENT SCRIPTS")
    logger.info(ctx.deps.current_scripts.keys())
    logger.info("RUNNING CODE")
    logger.info(script_to_run)

    out, err = await run_python_code_in_container(script_to_run, container_name=ctx.deps.container_name)

    logger.info("OUT")
    logger.info(out)
    logger.info("ERR")
    logger.info(err)

    for testing_dir in testing_dirs:
        shutil.rmtree(testing_dir, ignore_errors=True)

    if ctx.deps.log_code:
        await ctx.deps.log_code(CodeForLog(
            code=script,
            filename=file_name,
            output=out,
            error=err
        ))

    if err:
        logger.info(f"Error executing code: {err}")
        raise ModelRetry(f"Error executing code: {err}")

    new_scripts = []
    if ctx.deps.new_scripts:
        for new_script_name in ctx.deps.new_scripts:
            new_script = ctx.deps.current_scripts[new_script_name]
            new_scripts.append(NewScript(
                filename=new_script_name, script=new_script))

    modified_scripts = []
    if ctx.deps.modified_scripts_old_to_new_name:
        for original_script_name, new_script_name in ctx.deps.modified_scripts_old_to_new_name.items():

            original_fn = next(
                (f for f in ctx.deps.functions_injected if f.implementation_script.filename == original_script_name), None)
            original_mdl = next(
                (me for me in ctx.deps.model_entities_injected if me.implementation.model_implementation.implementation_script.filename == original_script_name), None)

            if original_fn:
                with open(original_fn.implementation_script.path, "r") as f:
                    original_script = f.read()
            elif original_mdl:
                with open(original_mdl.implementation.model_implementation.implementation_script.path, "r") as f:
                    original_script = f.read()
            else:
                raise RuntimeError(
                    f"Original script {original_script_name} which has been modified not found in injected functions or models")

            script_type = "model" if original_mdl else "function"

            modified_script = ctx.deps.current_scripts[new_script_name]
            modified_scripts.append(ModifiedScript(
                original_filename=original_script_name,
                new_filename=new_script_name,
                original_script=original_script,
                new_script=modified_script,
                type=script_type
            ))

    main_script = NewScript(filename=file_name, script=script)

    implementation = Implementation(conversation_id=ctx.deps.conversation_id,
                                    main_script=main_script,
                                    run_output=out,
                                    modified_scripts=modified_scripts,
                                    new_scripts=new_scripts)

    feedback = await submit_swe_result_approval_request(ctx.deps.client, implementation)

    if not feedback.approved:
        raise ModelRetry(
            f"Submission rejected with feedback: {feedback.feedback}")

    return ImplementationSummaryOutputWithImplementation(
        **result.model_dump(),
        implementation=implementation,
        functions_used=list(set(ctx.deps.functions_loaded))
    )
