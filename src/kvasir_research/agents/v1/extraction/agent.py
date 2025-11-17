from uuid import UUID
from typing import Literal, Optional
from pydantic_ai import Agent, RunContext
from pydantic_ai.models import ModelSettings

from kvasir_research.agents.v1.extraction.deps import ExtractionDeps
from kvasir_research.agents.v1.extraction.tools import extraction_toolset
from kvasir_research.agents.v1.shared_tools import navigation_toolset
from kvasir_research.agents.v1.extraction.prompt import EXTRACTION_AGENT_SYSTEM_PROMPT
from kvasir_research.utils.agent_utils import get_model
from kvasir_research.agents.abstract_agent import AbstractAgent
from kvasir_research.agents.v1.callbacks import KvasirV1Callbacks


model = get_model()


extraction_agent = Agent[ExtractionDeps, str](
    model,
    deps_type=ExtractionDeps,
    system_prompt=EXTRACTION_AGENT_SYSTEM_PROMPT,
    toolsets=[navigation_toolset, extraction_toolset],
    model_settings=ModelSettings(temperature=0),
    retries=5
)


@extraction_agent.system_prompt
async def extraction_agent_system_prompt(ctx: RunContext[ExtractionDeps]) -> str:
    if not ctx.deps:
        return EXTRACTION_AGENT_SYSTEM_PROMPT

    folder_structure_section = await ctx.deps.sandbox.get_folder_structure()
    project_description = await ctx.deps.callbacks.ontology.describe_mount_group()

    full_prompt = (
        f"{EXTRACTION_AGENT_SYSTEM_PROMPT}\n\n" +
        f"{folder_structure_section}\n\n" +
        "THE FOLLOWING IS THE PROJECT DESCRIPTION AND THE CURRENT ENTITY GRAPH. PAY CLOSE ATTENTION TO THE EXISTING STRUCTURE BEFORE MAKING CHANGES.\n\n" +
        f"{project_description}\n\n"
    )

    return full_prompt


class ExtractionAgentV1(AbstractAgent):

    def __init__(
        self,
        project_id: UUID,
        package_name: str,
        sandbox_type: Literal["local", "modal"],
        callbacks: KvasirV1Callbacks,
        run_id: Optional[UUID] = None
    ):
        super().__init__(project_id, package_name, sandbox_type, callbacks, run_id)

    async def __call__(self, prompt: str) -> str:
        try:
            if self.run_id is None:
                self.run_id = await self.callbacks.create_run(run_type="extraction")

            await self.callbacks.set_run_status(self.run_id, "running")

            deps = ExtractionDeps(
                run_id=self.run_id,
                project_id=self.project_id,
                package_name=self.package_name,
                sandbox_type=self.sandbox_type,
                callbacks=self.callbacks
            )

            response = await extraction_agent.run(
                f"{prompt}\n\nRespond with a summary of what you did.",
                deps=deps,
                message_history=await self.callbacks.get_message_history(self.run_id)
            )
            return response.output

        except Exception as e:
            if self.run_id:
                await self.callbacks.fail_run(self.run_id, f"Error running extraction agent: {e}")
            raise e
