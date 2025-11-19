from uuid import UUID
from typing import Literal, Optional, Annotated
from typing_extensions import Self
from taskiq import Context, TaskiqDepends
from pydantic_ai import Agent, RunContext
from pydantic_ai.models import ModelSettings

from kvasir_research.agents.v1.extraction.deps import ExtractionDeps
from kvasir_research.agents.v1.extraction.tools import extraction_toolset
from kvasir_research.agents.v1.shared_tools import navigation_toolset
from kvasir_research.agents.v1.extraction.prompt import EXTRACTION_AGENT_SYSTEM_PROMPT
from kvasir_research.agents.v1.base_agent import AgentV1
from kvasir_research.agents.v1.callbacks import KvasirV1Callbacks
from kvasir_research.agents.v1.broker import v1_broker
from kvasir_research.agents.v1.data_model import RunBase, RunCreate
from kvasir_research.utils.agent_utils import get_model

model = get_model()


extraction_agent = Agent[ExtractionDeps, str](
    model,
    deps_type=ExtractionDeps,
    toolsets=[navigation_toolset, extraction_toolset],
    retries=5,
    model_settings=ModelSettings(temperature=0)
)


@extraction_agent.system_prompt
async def extraction_agent_system_prompt(ctx: RunContext[ExtractionDeps]) -> str:
    folder_structure_section = await ctx.deps.sandbox.get_folder_structure()
    project_description = await ctx.deps.ontology.describe_mount_group()

    full_prompt = (
        f"{EXTRACTION_AGENT_SYSTEM_PROMPT}\n\n" +
        f"{folder_structure_section}\n\n" +
        "THE FOLLOWING IS THE PROJECT DESCRIPTION AND THE CURRENT ENTITY GRAPH. PAY CLOSE ATTENTION TO THE EXISTING STRUCTURE BEFORE MAKING CHANGES.\n\n" +
        f"{project_description}\n\n"
    )

    return full_prompt


class ExtractionAgentV1(AgentV1[ExtractionDeps, str]):
    deps_class = ExtractionDeps
    deps: ExtractionDeps

    def __init__(self, deps: ExtractionDeps):
        super().__init__(deps, extraction_agent)

    async def _setup_run(self) -> UUID:
        if self.deps.run_id is None:
            run = await self.deps.callbacks.create_run(
                self.deps.user_id,
                RunCreate(
                    type="extraction",
                    project_id=self.deps.project_id,
                    run_name=self.deps.run_name or "Extraction Run"
                )
            )
            self.deps.run_id = run.id

        await self.deps.callbacks.set_run_status(self.deps.user_id, self.deps.run_id, "running")
        return self.deps.run_id

    @classmethod
    async def from_run(cls, user_id: UUID, run_id: UUID, callbacks: KvasirV1Callbacks, bearer_token: Optional[str] = None) -> Self:
        return await super().from_run(user_id, run_id, callbacks, bearer_token)

    async def __call__(self, prompt: str) -> str:
        try:
            await self._setup_run()
            output = await self._run_agent(f"{prompt}\n\nRespond with a summary of what you did.")
            await self.finish_run("Extraction agent completed")
            return output

        except Exception as e:
            await self.fail_run_if_exists(f"Error running extraction agent: {e}")
            raise e


@v1_broker.task
async def run_extraction_agent(
    prompt: str,
    user_id: UUID,
    project_id: UUID,
    package_name: str,
    sandbox_type: Literal["local", "modal"],
    bearer_token: Optional[str],
    context: Annotated[Context, TaskiqDepends()]
) -> str:
    callbacks: KvasirV1Callbacks = context.state.callbacks

    deps = ExtractionDeps(
        user_id=user_id,
        project_id=project_id,
        package_name=package_name,
        sandbox_type=sandbox_type,
        callbacks=callbacks,
        bearer_token=bearer_token
    )
    extraction_agent = ExtractionAgentV1(deps)
    return await extraction_agent(prompt)
