from uuid import UUID
from pydantic_ai import Agent
from pydantic_ai.models import ModelSettings
from typing import Literal, Optional, Annotated
from taskiq import Context as TaskiqContext, TaskiqDepends

from kvasir_agents.agents.v1.extraction.deps import ExtractionDeps
from kvasir_agents.agents.v1.extraction.tools import extraction_toolset
from kvasir_agents.agents.v1.shared_tools import navigation_toolset
from kvasir_agents.agents.v1.extraction.prompt import EXTRACTION_AGENT_SYSTEM_PROMPT
from kvasir_agents.agents.v1.base_agent import AgentV1, Context
from kvasir_agents.agents.v1.callbacks import KvasirV1Callbacks
from kvasir_agents.agents.v1.broker import v1_broker
from kvasir_agents.agents.v1.data_model import RunCreate
from kvasir_agents.utils.agent_utils import get_model
from kvasir_agents.agents.v1.history_processors import (
    keep_only_most_recent_project_description,
    keep_only_most_recent_folder_structure,
    keep_only_most_recent_entity_context,
    keep_only_most_recent_mount_group
)

model = get_model()


extraction_agent = Agent[ExtractionDeps, str](
    model,
    deps_type=ExtractionDeps,
    system_prompt=EXTRACTION_AGENT_SYSTEM_PROMPT,
    toolsets=[navigation_toolset, extraction_toolset],
    retries=5,
    history_processors=[
        keep_only_most_recent_project_description,
        keep_only_most_recent_folder_structure,
        keep_only_most_recent_entity_context,
        keep_only_most_recent_mount_group
    ],
    model_settings=ModelSettings(temperature=0)
)


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


@v1_broker.task
async def run_extraction_agent(
    prompt: str,
    user_id: UUID,
    project_id: UUID,
    package_name: str,
    sandbox_type: Literal["local", "modal"],
    bearer_token: Optional[str],
    taskiq_context: Annotated[TaskiqContext, TaskiqDepends()],
    context: Optional[Context] = None,
) -> str:
    callbacks: KvasirV1Callbacks = taskiq_context.state.callbacks

    deps = ExtractionDeps(
        user_id=user_id,
        project_id=project_id,
        package_name=package_name,
        sandbox_type=sandbox_type,
        callbacks=callbacks,
        bearer_token=bearer_token
    )
    extraction_agent = ExtractionAgentV1(deps)
    mount_group_description = f"<project_description>\n\n{await deps.ontology.describe_mount_group(include_positions=True)}\n\n</project_description>"
    folder_structure = f"<folder_structure>\n\n{await deps.sandbox.get_folder_structure()}\n\n</folder_structure>"
    return await extraction_agent(prompt, context=context, injections=[mount_group_description, folder_structure])
