import ast
from pydantic_ai import Agent, RunContext, ModelRetry
from dataclasses import dataclass
from typing import Literal, List
from synesis_api.base_schema import BaseSchema
from synesis_api.utils import run_python_code_in_container
from synesis_api.modules.model_integration.agent.model_analysis_agent.prompt import REPO_ANALYSIS_SYSTEM_PROMPT
from synesis_api.modules.model_integration.agent.shared_tools import (
    get_repo_info,
    get_repo_structure,
    get_file_content,
    get_input_structure,
    get_output_structure
)
from synesis_api.modules.model_integration.agent.shared_tools import get_base_config_definition_code
from synesis_api.modules.model_integration.agent.prepare_tools import filter_tools_by_source
from synesis_api.utils import get_model
from synesis_api.modules.model_integration.agent.output_structures import get_supported_tasks, get_supported_modalities
from synesis_api.modules.model_integration.agent.base_deps import BaseDeps


@dataclass(kw_only=True)
class ModelAnalysisDeps(BaseDeps):
    python_version: str


class ModelAnalysisAgentOutput(BaseSchema):
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
    model_config_parameters: List[str]
    model_input_description: str
    model_output_description: str
    training_algorithm_description: str
    training_algorithm_parameters: List[str]


model = get_model()

model_analysis_agent = Agent(
    model,
    deps_type=ModelAnalysisDeps,
    output_type=ModelAnalysisAgentOutput,
    tools=[
        get_repo_info,
        get_repo_structure,
        get_file_content,
        get_input_structure,
        get_output_structure
    ],
    prepare_tools=filter_tools_by_source,
    retries=3
)


@model_analysis_agent.system_prompt
def get_model_analysis_system_prompt(ctx: RunContext[ModelAnalysisDeps]) -> str:

    if ctx.deps.source == "github":
        return f"{REPO_ANALYSIS_SYSTEM_PROMPT}\n\n GITHUB URL: {ctx.deps.model_id}\n\n PYTHON VERSION: {ctx.deps.python_version}"
    elif ctx.deps.source == "pip":
        return f"{REPO_ANALYSIS_SYSTEM_PROMPT}\n\n PIP PACKAGE: {ctx.deps.model_id}\n\n PYTHON VERSION: {ctx.deps.python_version}"


@model_analysis_agent.output_validator
async def validate_model_analysis_output(
        ctx: RunContext[ModelAnalysisDeps],
        result: ModelAnalysisAgentOutput) -> ModelAnalysisAgentOutput:
    """
    Validate the repo analysis output.

    Args:
        ctx: The context.
        result: The repo analysis output.

    Returns:
        RepoAnalysisAgentOutput: The validated repo analysis output.
    """

    print("CALLING VALIDATE MODEL ANALYSIS OUTPUT")
    print(f"Modality: {result.modality}")
    print(f"Supported tasks: {result.supported_tasks}")
    print("@"*50)

    supported_modalities = get_supported_modalities()
    if result.modality not in supported_modalities:
        raise ModelRetry(
            f"Modality {result.modality} not supported, choose from {supported_modalities}")

    modality_supported_tasks = get_supported_tasks(result.modality)
    if set(result.supported_tasks) - set(modality_supported_tasks):
        raise ModelRetry(
            f"Task(s) {set(result.supported_tasks) - set(modality_supported_tasks)} not supported for modality {result.modality}")

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

    # Run the config code to make sure it is valid
    _, err = await run_python_code_in_container(
        result.config_code,
        container_name=ctx.deps.container_name,
        cwd=ctx.deps.cwd
    )

    if err:
        print("@"*20, "ERROR RUNNING CONFIG CODE", "@"*20)
        print(f"Error: {err}")
        print("@"*50)
        raise ModelRetry(f"Error running config code: {err}")

    return result
