import ast
from typing import List, Literal
from pydantic_ai import RunContext, ModelRetry

from synesis_api.base_schema import BaseSchema
from synesis_api.utils.code_utils import run_python_code_in_container, remove_line_numbers_from_script
from synesis_api.agents.model_integration.output_structures import get_supported_tasks, get_supported_modalities, get_validation_code
from synesis_api.agents.model_integration.synthetic_data_code import get_synthetic_data, get_synthetic_config
from synesis_api.agents.model_integration.shared_tools import get_base_config_definition_code
from synesis_api.agents.model_integration.deps import ModelIntegrationDeps


# Schema outputs

class ModelAnalysisOutput(BaseSchema):
    repo_name: str
    repo_description: str
    config_code: str
    supported_tasks: List[Literal["classification",
                                  "regression",
                                  "segmentation",
                                  "forecasting"]]
    modality: Literal["time_series", "image", "text"]
    model_name: str
    model_description: str
    config_parameters: List[str]
    model_input_description: str
    model_output_description: str


class ImplementationPlanningOutput(BaseSchema):
    input_structure_description: str
    output_structure_description: str
    input_transformation_plan: str
    model_application_plan: str
    output_transformation_plan: str
    training_plan: str
    inference_plan: str


class TrainingOutput(BaseSchema):
    code_explanation: str


class TrainingOutputWithScript(TrainingOutput):
    script: str


class InferenceOutput(BaseSchema):
    code_explanation: str


class InferenceOutputWithScript(InferenceOutput):
    script: str


# Function outputs

async def submit_model_analysis_output(
    ctx: RunContext[ModelIntegrationDeps],
    result: ModelAnalysisOutput
) -> ModelAnalysisOutput:

    if not ctx.deps.stage == "model_analysis":
        raise ModelRetry(f"Invalid output for current stage: {ctx.deps.stage}")

    # Validate modality
    supported_modalities = get_supported_modalities()
    if result.modality not in supported_modalities:
        raise ModelRetry(
            f"Modality {result.modality} not supported, choose from {supported_modalities}")

    # Validate supported tasks for the modality
    modality_supported_tasks = get_supported_tasks(result.modality)
    if set(result.supported_tasks) - set(modality_supported_tasks):
        raise ModelRetry(
            f"Task(s) {set(result.supported_tasks) - set(modality_supported_tasks)} not supported for modality {result.modality}.\n"
            f"Supported tasks for modality {result.modality} are {modality_supported_tasks}.")

    # Process config code by merging with base config definition
    base_config_definition_code = get_base_config_definition_code()
    base_fields = set()

    for node in ast.walk(ast.parse(base_config_definition_code)):
        if isinstance(node, ast.ClassDef):
            for child_node in node.body:
                if isinstance(child_node, ast.AnnAssign):
                    base_fields.add(child_node.target.id)
                elif isinstance(child_node, ast.Assign):
                    for target in child_node.targets:
                        if isinstance(target, ast.Name):
                            base_fields.add(target.id)

    filtered_config_code = "\n".join(
        [line for line in result.config_code.split("\n") if not any(field in line for field in base_fields)])
    result.config_code = f"{base_config_definition_code}\n\n{filtered_config_code}"

    # Validate config code by running it
    _, err = await run_python_code_in_container(
        result.config_code,
        container_name=ctx.deps.container_name,
        cwd=ctx.deps.cwd
    )

    if err:
        raise ModelRetry(f"Error running config code: {err}")

    return result


async def submit_implementation_planning_output(
    ctx: RunContext[ModelIntegrationDeps],
    result: ImplementationPlanningOutput
) -> ImplementationPlanningOutput:

    if not ctx.deps.stage == "implementation_planning":
        raise ModelRetry(f"Invalid output for current stage: {ctx.deps.stage}")

    return result


async def submit_training_output(
    ctx: RunContext[ModelIntegrationDeps],
    result: TrainingOutput
) -> TrainingOutputWithScript:

    if not ctx.deps.stage == "training":
        raise ModelRetry(f"Invalid output for current stage: {ctx.deps.stage}")

    # Check if script was written
    if not ctx.deps.current_script:
        raise ModelRetry("No training script written")

    # Get synthetic data and config for testing
    synthetic_data_code = get_synthetic_data(
        modality=ctx.deps.modality,
        task_name=ctx.deps.current_task
    )

    synthetic_config_code = get_synthetic_config()

    script = remove_line_numbers_from_script(ctx.deps.current_script)

    test_code = (
        f"{script}\n\n"
        f"{synthetic_data_code}\n\n"
        f"{synthetic_config_code}\n\n"
        f"prepare_training_data(miya_data, config, '{ctx.deps.integration_id}', miya_metadata, miya_labels, miya_segmentation_labels)\n"
        f"train_model(miya_data, config, '{ctx.deps.integration_id}', miya_metadata, miya_labels, miya_segmentation_labels)\n"
    )

    _, err = await run_python_code_in_container(
        test_code,
        container_name=ctx.deps.container_name,
        cwd=ctx.deps.cwd
    )

    if err:
        raise ModelRetry(f"Error executing training script: {err}")

    return TrainingOutputWithScript(**result.model_dump(), script=script)


async def submit_inference_output(
    ctx: RunContext[ModelIntegrationDeps],
    result: InferenceOutput
) -> InferenceOutputWithScript:

    if not ctx.deps.stage == "inference":
        raise ModelRetry(f"Invalid output for current stage: {ctx.deps.stage}")

    # Check if script was written
    if not ctx.deps.current_script:
        raise ModelRetry("No inference script written")

    # Get synthetic data, config, and validation code for testing
    synthetic_data_code = get_synthetic_data(
        modality=ctx.deps.modality,
        task_name=ctx.deps.current_task
    )

    synthetic_config_code = get_synthetic_config()

    validation_code = get_validation_code(
        modality=ctx.deps.modality,
        task_name=ctx.deps.current_task
    )

    script = remove_line_numbers_from_script(ctx.deps.current_script)

    test_code = (
        f"{script}\n\n"
        f"{synthetic_data_code}\n\n"
        f"{synthetic_config_code}\n\n"
        f"{validation_code}\n\n"
        f"output = run_inference(miya_data, config, '{ctx.deps.integration_id}', miya_metadata, miya_labels, miya_segmentation_labels)\n\n"
        f"validate_inference_output(output)"
    )

    _, err = await run_python_code_in_container(
        test_code,
        container_name=ctx.deps.container_name,
        cwd=ctx.deps.cwd
    )

    if err:
        raise ModelRetry(f"Error executing inference script: {err}")

    return InferenceOutputWithScript(**result.model_dump(), script=script)
