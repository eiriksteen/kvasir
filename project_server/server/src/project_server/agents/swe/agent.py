from pydantic_ai import Agent, RunContext
from pydantic_ai.models import ModelSettings

from project_server.agents.swe.prompt import SWE_AGENT_BASE_SYSTEM_PROMPT
from project_server.agents.swe.deps import SWEAgentDeps
from project_server.agents.swe.tools import file_editing_toolset
from project_server.agents.shared_tools import get_task_guidelines_tool, execute_python_code, navigation_toolset
from project_server.agents.swe.history_processors import keep_only_most_recent_script
from project_server.utils.agent_utils import (
    get_model,
    get_injected_entities_description,
    get_sandbox_environment_description,
    get_project_description,
    get_working_directory_description
)
from project_server.worker import logger


model = get_model()


swe_agent = Agent[SWEAgentDeps, str](
    model,
    deps_type=SWEAgentDeps,
    system_prompt=SWE_AGENT_BASE_SYSTEM_PROMPT,
    tools=[get_task_guidelines_tool, execute_python_code],
    toolsets=[navigation_toolset, file_editing_toolset],
    retries=3,
    history_processors=[keep_only_most_recent_script],
    model_settings=ModelSettings(temperature=0)
)


@swe_agent.system_prompt
async def swe_agent_system_prompt(ctx: RunContext[SWEAgentDeps]) -> str:

    if not ctx.deps:
        return SWE_AGENT_BASE_SYSTEM_PROMPT

    project_description = get_project_description(ctx.deps.project)
    working_directory_section = await get_working_directory_description(ctx.deps.container_name)
    entities_description = get_injected_entities_description(
        ctx.deps.data_sources_injected,
        ctx.deps.datasets_injected,
        ctx.deps.model_entities_injected,
        ctx.deps.analyses_injected,
        ctx.deps.pipelines_injected
    )
    env_description = get_sandbox_environment_description()

    full_prompt = (
        f"{SWE_AGENT_BASE_SYSTEM_PROMPT}\n\n" +
        f"{project_description}\n\n" +
        f"{entities_description}\n\n" +
        f"{env_description}\n\n" +
        f"{working_directory_section}\n\n"
    )

    logger.info(
        f"SWE agent system prompt:\n\n{full_prompt}")

    return full_prompt
