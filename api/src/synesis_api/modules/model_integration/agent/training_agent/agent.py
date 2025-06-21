from pydantic_ai import Agent, RunContext, ModelRetry
from dataclasses import dataclass
from typing import Literal
from synesis_api.base_schema import BaseSchema
from synesis_api.utils import (
    get_model,
    run_python_code_in_container,
    remove_line_numbers_from_script
)
from synesis_api.modules.model_integration.agent.training_agent.prompt import TRAINING_SYSTEM_PROMPT
from synesis_api.modules.model_integration.agent.model_analysis_agent.agent import ModelAnalysisAgentOutput
from synesis_api.modules.model_integration.agent.shared_tools import (
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
from synesis_api.modules.model_integration.agent.synthetic_data_code import get_synthetic_data, get_synthetic_config
from synesis_api.modules.model_integration.agent.prepare_tools import filter_tools_by_source
from synesis_api.modules.model_integration.agent.base_deps import BaseDeps
from synesis_api.modules.model_integration.agent.history_processors import keep_only_most_recent_script, summarize_message_history


@dataclass(kw_only=True)
class TrainingDeps(BaseDeps):
    current_task: Literal[
        "classification",
        "regression",
        "segmentation",
        "forecasting"]
    modality: Literal["time_series", "image", "text"]
    model_analysis: ModelAnalysisAgentOutput
    implementation_plan: str


class TrainingAgentOutput(BaseSchema):
    code_explanation: str


class TrainingAgentOutputWithScript(TrainingAgentOutput):
    script: str


model = get_model()


training_agent = Agent(
    model,
    deps_type=TrainingDeps,
    output_type=TrainingAgentOutput,
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
    retries=5,
    history_processors=[keep_only_most_recent_script,
                        summarize_message_history]
)


@training_agent.system_prompt
async def get_training_system_prompt(ctx: RunContext[TrainingDeps]) -> str:
    return f"""
    {TRAINING_SYSTEM_PROMPT} 
    
    Here is useful information for writing the training script:

    <begin_context>

    CURRENT TASK: {ctx.deps.current_task}

    {'GITHUB URL' if ctx.deps.source == 'github' else 'PIP PACKAGE'}: {ctx.deps.model_id}

    REPO DESCRIPTION: {ctx.deps.model_analysis.repo_description}

    MODEL DESCRIPTION: {ctx.deps.model_analysis.model_description}

    TRAINING ALGORITHM DESCRIPTION: {ctx.deps.model_analysis.training_algorithm_description}

    MODEL CONFIGURATION CODE (config.py): {ctx.deps.model_analysis.config_code}

    INPUT STRUCTURE: {get_input_structure(ctx.deps.modality)}
    
    OUTPUT STRUCTURE: {get_output_structure(ctx.deps.modality, ctx.deps.current_task)}

    IMPLEMENTATION PLAN: {ctx.deps.implementation_plan}

    <end_context>
    """


@training_agent.output_validator
async def validate_training_output(
        ctx: RunContext[TrainingDeps],
        result: TrainingAgentOutput) -> TrainingAgentOutputWithScript:
    """
    Validate and execute the training script.

    Args:
        ctx: The context.
        result: The training output.

    Returns:
        TrainingOutput: The training output.
    """
    if not ctx.deps.current_script:
        raise ModelRetry("No script written")

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

    print("CALLING TRAINING TEST CODE")
    print("@"*50)

    _, err = await run_python_code_in_container(
        test_code,
        container_name=ctx.deps.container_name,
        cwd=ctx.deps.cwd
    )

    if err:
        print("@"*20, "ERROR EXECUTING TRAINING SCRIPT", "@"*20)
        print(f"Error: {err}")
        print("@"*50)
        raise ModelRetry(f"Error executing training script: {err}")

    print("@"*20, "TRAINING SCRIPT EXECUTED SUCCESSFULLY", "@"*20)

    return TrainingAgentOutputWithScript(
        **result.model_dump(),
        script=script
    )
