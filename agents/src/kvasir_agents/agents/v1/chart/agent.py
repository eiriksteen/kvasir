from uuid import UUID
from typing import Optional
from pydantic_ai import Agent, RunContext
from pydantic_ai.models import ModelSettings

from kvasir_agents.agents.v1.chart.deps import ChartDeps
from kvasir_agents.agents.v1.chart.output import submit_chart
from kvasir_agents.agents.v1.chart.prompt import CHART_AGENT_SYSTEM_PROMPT
from kvasir_agents.agents.v1.shared_tools import navigation_toolset
from kvasir_agents.agents.v1.chart.output import ChartAgentOutput
from kvasir_agents.agents.v1.base_agent import AgentV1, Context
from kvasir_agents.agents.v1.data_model import RunCreate
from kvasir_agents.utils.agent_utils import get_model
from kvasir_agents.agents.v1.history_processors import (
    keep_only_most_recent_project_description,
    keep_only_most_recent_folder_structure,
    keep_only_most_recent_entity_context
)


model = get_model()


chart_agent = Agent[ChartDeps, ChartAgentOutput](
    model,
    deps_type=ChartDeps,
    toolsets=[navigation_toolset],
    output_type=submit_chart,
    retries=5,
    history_processors=[
        keep_only_most_recent_project_description,
        keep_only_most_recent_folder_structure,
        keep_only_most_recent_entity_context
    ],
    model_settings=ModelSettings(temperature=0)
)


@chart_agent.system_prompt
async def chart_agent_system_prompt(ctx: RunContext[ChartDeps]) -> str:
    env_description = ctx.deps.sandbox.get_pyproject_for_env_description()
    object_group_description = ""
    if ctx.deps.object_group is not None:
        object_group_description = (
            "\n<object_group>\n"
            f"The target object group is: {ctx.deps.object_group.name}\n"
            f"The target object group description is: {ctx.deps.object_group.description}\n"
            "</object_group>\n\n"
        )

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
        f"{env_description}\n\n"
        f"{object_group_description}\n\n"
        f"{base_code_context}\n\n"
    )

    return full_prompt


class ChartAgentV1(AgentV1[ChartDeps, ChartAgentOutput]):
    deps_class = ChartDeps
    deps: ChartDeps

    def __init__(self, deps: ChartDeps):
        super().__init__(deps, chart_agent)

    async def _setup_run(self) -> UUID:
        if self.deps.run_id is None:
            run = await self.deps.callbacks.create_run(
                self.deps.user_id,
                RunCreate(
                    type="chart",
                    project_id=self.deps.project_id,
                    run_name=self.deps.run_name or "Chart Run"
                )
            )
            self.deps.run_id = run.id

        await self.deps.callbacks.set_run_status(self.deps.user_id, self.deps.run_id, "running")
        return self.deps.run_id

    async def __call__(self, prompt: str, context: Optional[Context] = None) -> ChartAgentOutput:
        mount_group_description = f"<project_description>\n\n{await self.deps.ontology.describe_mount_group(include_positions=False)}\n\n</project_description>"
        return await super().__call__(prompt, context, injections=[mount_group_description])
