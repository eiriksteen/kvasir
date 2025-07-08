from pydantic_ai import Agent, RunContext, ModelRetry
from pydantic_ai.settings import ModelSettings
from dataclasses import dataclass
from typing import Literal
from synesis_api.base_schema import BaseSchema
from synesis_api.utils import (
    get_model,
    run_python_code_in_container,
    remove_line_numbers_from_script
)
from synesis_api.agents.model_integration.inference_agent.prompt import INFERENCE_SYSTEM_PROMPT
from synesis_api.agents.model_integration.model_analysis_agent.agent import ModelAnalysisAgentOutput
from synesis_api.agents.model_integration.shared_tools import (
    get_repo_info,
    get_repo_structure,
    get_file_content,
    get_input_structure,
    get_output_structure,
    write_script,
    replace_script_lines,
    add_script_lines,
    delete_script_lines
)
from synesis_api.agents.model_integration.synthetic_data_code import get_synthetic_data, get_synthetic_config
from synesis_api.agents.model_integration.output_structures import get_validation_code
from synesis_api.agents.model_integration.prepare_tools import filter_tools_by_source
from synesis_api.agents.model_integration.base_deps import BaseDeps
from synesis_api.agents.model_integration.history_processors import keep_only_most_recent_script, summarize_message_history


@dataclass(kw_only=True)
class InferenceDeps(BaseDeps):
    training_script: str
    implementation_plan: str
    current_task: Literal[
        "classification",
        "regression",
        "segmentation",
        "forecasting"]
    modality: Literal["time_series", "image", "text"]
    model_analysis: ModelAnalysisAgentOutput


class InferenceAgentOutput(BaseSchema):
    code_explanation: str


class InferenceAgentOutputWithScript(InferenceAgentOutput):
    script: str


model = get_model()

inference_agent = Agent(
    model,
    deps_type=InferenceDeps,
    output_type=InferenceAgentOutput,
    tools=[
        get_repo_info,
        get_repo_structure,
        get_file_content,
        write_script,
        replace_script_lines,
        add_script_lines,
        delete_script_lines
    ],
    prepare_tools=filter_tools_by_source,
    retries=10,
    history_processors=[keep_only_most_recent_script,
                        # summarize_message_history
                        ],
    model_settings=ModelSettings(temperature=0),
)


@inference_agent.system_prompt
async def get_inference_system_prompt(ctx: RunContext[InferenceDeps]) -> str:
    return f"""
    {INFERENCE_SYSTEM_PROMPT}

    Here is useful information for writing the inference script:

    <begin_context>

    CURRENT TASK: {ctx.deps.current_task}

    TRAINING SCRIPT: {ctx.deps.training_script}

    {'GITHUB URL' if ctx.deps.source == 'github' else 'PIP PACKAGE'}: {ctx.deps.model_id}

    REPO DESCRIPTION: {ctx.deps.model_analysis.repo_description}

    MODEL DESCRIPTION: {ctx.deps.model_analysis.model_description}

    MODEL CONFIGURATION CODE (config.py): {ctx.deps.model_analysis.config_code}

    INPUT STRUCTURE: {get_input_structure(ctx.deps.modality)}

    OUTPUT STRUCTURE: {get_output_structure(ctx.deps.modality, ctx.deps.current_task)}

    IMPLEMENTATION PLAN: {ctx.deps.implementation_plan}

    <end_context>
    """


@inference_agent.output_validator
async def validate_inference_output(
        ctx: RunContext[InferenceDeps],
        result: InferenceAgentOutput) -> InferenceAgentOutputWithScript:
    """
    Validate and execute the inference script.

    Args:
        ctx: The context.
        result: The inference output.

    Returns:
        InferenceOutput: The inference output.
    """
    if not ctx.deps.current_script:
        raise ModelRetry("No script written")

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

    return InferenceAgentOutputWithScript(
        **result.model_dump(),
        script=script
    )
