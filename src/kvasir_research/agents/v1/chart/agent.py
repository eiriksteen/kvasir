from pydantic_ai import Agent, RunContext
from pydantic_ai.models import ModelSettings

from project_server.agents.chart.deps import ChartDeps
from project_server.agents.chart.output import submit_chart
from project_server.agents.chart.prompt import CHART_AGENT_SYSTEM_PROMPT
from project_server.agents.shared_tools import navigation_toolset
from project_server.utils.agent_utils import (
    get_model,
    get_entities_description,
    get_sandbox_environment_description,
    get_working_directory_description
)
from project_server.agents.chart.output import ChartAgentOutput
from project_server.worker import logger


model = get_model()


chart_agent = Agent[ChartDeps, ChartAgentOutput](
    model,
    deps_type=ChartDeps,
    system_prompt=CHART_AGENT_SYSTEM_PROMPT,
    output_type=submit_chart,
    toolsets=[navigation_toolset],
    model_settings=ModelSettings(temperature=0),
    retries=5
)


@chart_agent.system_prompt
async def chart_agent_system_prompt(ctx: RunContext[ChartDeps]) -> str:
    if not ctx.deps:
        return CHART_AGENT_SYSTEM_PROMPT

    # Get entity descriptions using the shared utility
    entities_description = await get_entities_description(
        ctx.deps.client,
        ctx.deps.data_sources_injected,
        ctx.deps.datasets_injected,
        [],  # model entities
        [],  # analyses
        []   # pipelines
    )

    env_description = get_sandbox_environment_description()
    cwd_description = await get_working_directory_description(ctx.deps.container_name)
    object_group_description = ""
    if ctx.deps.object_group is not None:
        object_group_description = (
            "\n<object_group>\n"
            f"The target object group is: {ctx.deps.object_group.name}\n"
            f"The target object group description is: {ctx.deps.object_group.description}\n"
            "</object_group>\n\n"
        )

    # Add base_code context if available
    base_code_context = ""
    if ctx.deps.base_code:
        base_code_context = (
            "\n<base_code>\n"
            "The following code has already been executed and variables are available:\n\n"
            f"```python\n{ctx.deps.base_code}\n```\n"
            "</base_code>\n\n"
        )

    full_prompt = (
        f"{CHART_AGENT_SYSTEM_PROMPT}\n\n"
        f"{cwd_description}\n\n"
        f"{env_description}\n\n"
        f"{entities_description}\n\n"
        f"{object_group_description}\n\n"
        f"{base_code_context}\n\n"
    )

    # logger.info(f"Chart agent system prompt:\n\n{full_prompt}")

    return full_prompt
