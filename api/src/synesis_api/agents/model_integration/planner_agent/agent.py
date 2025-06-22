from pydantic_ai import Agent, RunContext
from pydantic_ai.settings import ModelSettings
from dataclasses import dataclass
from typing import Literal
from synesis_api.utils import get_model
from synesis_api.agents.model_integration.planner_agent.prompt import PLANNER_SYSTEM_PROMPT
from synesis_api.agents.model_integration.model_analysis_agent.agent import ModelAnalysisAgentOutput
from synesis_api.agents.model_integration.shared_tools import (
    get_repo_info,
    get_repo_structure,
    get_file_content,
    get_input_structure,
    get_output_structure
)
from synesis_api.agents.model_integration.prepare_tools import filter_tools_by_source
from synesis_api.agents.model_integration.base_deps import BaseDeps


@dataclass(kw_only=True)
class PlannerDeps(BaseDeps):
    current_task: Literal[
        "classification",
        "regression",
        "segmentation",
        "forecasting"]
    modality: Literal["time_series", "image", "text"]
    model_analysis: ModelAnalysisAgentOutput


model = get_model()


planning_agent = Agent(
    model,
    deps_type=PlannerDeps,
    output_type=str,
    system_prompt=PLANNER_SYSTEM_PROMPT,
    tools=[
        get_repo_info,
        get_repo_structure,
        get_file_content
    ],
    prepare_tools=filter_tools_by_source,
    model_settings=ModelSettings(temperature=0),
)


@planning_agent.system_prompt
def get_planner_planning_system_prompt(ctx: RunContext[PlannerDeps]) -> str:
    return f"""
    {PLANNER_SYSTEM_PROMPT}

    CURRENT TASK: {ctx.deps.current_task}

    {'GITHUB URL' if ctx.deps.source == 'github' else 'PIP PACKAGE'}: {ctx.deps.model_id}

    MODEL ANALYSIS (PAY ATTENTION TO THE CONFIGURATION PARAMETERS): {ctx.deps.model_analysis.model_dump_json()}

    INPUT STRUCTURE: {get_input_structure(ctx.deps.modality)}

    OUTPUT STRUCTURE: {get_output_structure(ctx.deps.modality, ctx.deps.current_task)}
    """


@planning_agent.output_validator
async def validate_planner_output(_: RunContext[PlannerDeps], result: str) -> str:
    print("PLANNER OUTPUT:")
    print(result)
    print("-"*50)
    return result
