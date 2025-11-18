from uuid import UUID
from typing import Literal, List, Optional
from pydantic_ai import Agent, RunContext
from pydantic_ai.models import ModelSettings

from kvasir_research.agents.v1.chart.deps import ChartDeps
from kvasir_research.agents.v1.chart.output import submit_chart
from kvasir_research.agents.v1.chart.prompt import CHART_AGENT_SYSTEM_PROMPT
from kvasir_research.agents.v1.shared_tools import navigation_toolset
from kvasir_research.utils.agent_utils import get_model
from kvasir_research.agents.v1.chart.output import ChartAgentOutput
from kvasir_research.agents.abstract_agent import AbstractAgent
from kvasir_ontology.entities.dataset.data_model import ObjectGroup
from kvasir_research.agents.v1.callbacks import KvasirV1Callbacks


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
    if ctx.deps is None:
        return CHART_AGENT_SYSTEM_PROMPT

    # Get entity descriptions
    entity_ids = [*ctx.deps.datasets_injected, *ctx.deps.data_sources_injected]
    entities_description = await ctx.deps.ontology.describe_entities(entity_ids)

    env_description = ctx.deps.sandbox.get_pyproject_for_env_description()
    folder_structure_description = await ctx.deps.sandbox.get_folder_structure()
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
        f"{folder_structure_description}\n\n"
        f"{env_description}\n\n"
        f"{entities_description}\n\n"
        f"{object_group_description}\n\n"
        f"{base_code_context}\n\n"
    )

    return full_prompt


class ChartAgentV1(AbstractAgent):

    def __init__(
        self,
        user_id: UUID,
        project_id: UUID,
        package_name: str,
        sandbox_type: Literal["local", "modal"],
        callbacks: KvasirV1Callbacks,
        datasets_injected: List[UUID] = None,
        data_sources_injected: List[UUID] = None,
        base_code: Optional[str] = None,
        object_group: Optional[ObjectGroup] = None,
        run_id: Optional[UUID] = None,
        bearer_token: Optional[str] = None
    ):
        super().__init__(
            user_id=user_id,
            project_id=project_id,
            package_name=package_name,
            sandbox_type=sandbox_type,
            callbacks=callbacks,
            bearer_token=bearer_token,
            run_id=run_id
        )
        self.datasets_injected = datasets_injected or []
        self.data_sources_injected = data_sources_injected or []
        self.base_code = base_code
        self.object_group = object_group

    async def __call__(self, prompt: str) -> ChartAgentOutput:
        try:
            if self.run_id is None:
                self.run_id = await self.callbacks.create_run(self.user_id, self.project_id, run_type="chart")

            await self.callbacks.set_run_status(self.run_id, "running")

            deps = ChartDeps(
                project_id=self.project_id,
                package_name=self.package_name,
                user_id=self.user_id,
                sandbox_type=self.sandbox_type,
                datasets_injected=self.datasets_injected,
                data_sources_injected=self.data_sources_injected,
                base_code=self.base_code,
                object_group=self.object_group,
                callbacks=self.callbacks,
                bearer_token=self.bearer_token
            )

            response = await chart_agent.run(
                prompt,
                deps=deps,
                message_history=await self.callbacks.get_message_history(self.run_id) if self.run_id else None
            )
            return response.output

        except Exception as e:
            if self.run_id:
                await self.callbacks.fail_run(self.run_id, f"Error running chart agent: {e}")
            raise e
