from pydantic_ai import Agent
from pydantic_ai.settings import ModelSettings
from pydantic_ai import RunContext

from project_server.agents.analysis.prompt import ANALYSIS_AGENT_SYSTEM_PROMPT
from project_server.utils.agent_utils import (
    get_model,
    get_entities_description,
    get_sandbox_environment_description
)
from project_server.agents.analysis.deps import AnalysisDeps
from project_server.agents.analysis.tools import (
    create_notebook_section,
    move_analysis_result,
    delete_notebook_section,
    edit_section_name,
    move_sections,
    generate_analysis_result
)
from project_server.worker import logger


model = get_model()

analysis_agent = Agent(
    model,
    system_prompt=ANALYSIS_AGENT_SYSTEM_PROMPT,
    deps_type=AnalysisDeps,
    name="Analysis Agent",
    model_settings=ModelSettings(temperature=0.1),
    retries=3,
    tools=[
        create_notebook_section,
        move_analysis_result,
        delete_notebook_section,
        edit_section_name,
        move_sections,
        generate_analysis_result
    ],
)


@analysis_agent.system_prompt
async def analysis_agent_system_prompt(ctx: RunContext[AnalysisDeps]) -> str:
    if not ctx.deps:
        return ANALYSIS_AGENT_SYSTEM_PROMPT

    entities_description = await get_entities_description(
        ctx.deps.client,
        ctx.deps.data_sources_injected,
        ctx.deps.datasets_injected,
        ctx.deps.model_instantiatedies_injected,
        ctx.deps.analyses_injected,
        []  # pipelines
    )

    env_description = get_sandbox_environment_description()

    final_prompt = (
        f"{ANALYSIS_AGENT_SYSTEM_PROMPT}\n\n" +
        f"{env_description}\n\n" +
        f"{entities_description}\n\n" +
        f"\n\nThe ID of the current analysis is: {ctx.deps.analysis_id}\n\n"
    )

    logger.info(f"Analysis agent system prompt: {final_prompt}")

    return final_prompt
