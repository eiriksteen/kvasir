from uuid import UUID
from typing import List, Optional
from pydantic_ai import Agent, RunContext
from pydantic_ai.models import ModelSettings

from kvasir_research.utils.agent_utils import get_model
from kvasir_research.agents.v1.history_processors import keep_only_most_recent_script
from kvasir_research.agents.v1.swe.deps import SWEDeps
from kvasir_research.agents.v1.swe.prompt import SWE_SYSTEM_PROMPT
from kvasir_research.agents.v1.kvasir.knowledge_bank import get_guidelines, SUPPORTED_TASKS_LITERAL
from kvasir_research.agents.v1.shared_tools import navigation_toolset, knowledge_bank_toolset
from kvasir_research.agents.v1.swe.tools import swe_toolset
from kvasir_research.agents.v1.swe.output import submit_implementation_results, submit_message_to_orchestrator
from kvasir_research.agents.v1.base_agent import AgentV1
from kvasir_ontology.entities.pipeline.data_model import PipelineCreate
from kvasir_research.agents.v1.extraction.agent import run_extraction_agent
from kvasir_research.agents.v1.history_processors import keep_only_most_recent_project_description, keep_only_most_recent_folder_structure, keep_only_most_recent_entity_context
from kvasir_research.agents.v1.base_agent import Context


model = get_model()


swe_agent = Agent[SWEDeps, str](
    model,
    deps_type=SWEDeps,
    toolsets=[navigation_toolset, knowledge_bank_toolset, swe_toolset],
    output_type=[
        submit_implementation_results,
        submit_message_to_orchestrator
    ],
    retries=5,
    history_processors=[
        keep_only_most_recent_script,
        keep_only_most_recent_project_description,
        keep_only_most_recent_folder_structure,
        keep_only_most_recent_entity_context
    ],
    model_settings=ModelSettings(temperature=0)
)


@swe_agent.system_prompt
async def swe_system_prompt(ctx: RunContext[SWEDeps]) -> str:
    current_wd = await ctx.deps.sandbox.get_working_directory()
    env_description = ctx.deps.sandbox.get_pyproject_for_env_description()

    if ctx.deps.guidelines:
        guidelines_content = "\n\n".join(
            [get_guidelines(task) for task in ctx.deps.guidelines])

    assert ctx.deps.pipeline_id is not None, "Pipeline ID must be set when the agent starts running"
    pipeline_desc = await ctx.deps.ontology.describe_entity(ctx.deps.pipeline_id, "pipeline", include_connections=True)

    full_system_prompt = (
        f"{SWE_SYSTEM_PROMPT}\n\n" +
        f"Package name: {ctx.deps.package_name}\n\n" +
        f"Current working directory: {current_wd}\n\n" +
        f"Data paths to use: {ctx.deps.data_paths}\n\n" +
        f"Read only paths: {ctx.deps.read_only_paths}\n\n" +
        f"You environment is described by the following pyproject.toml:\n\n<pyproject>\n{env_description}\n</pyproject>\n\n" +
        (f"Here are the task-specific guidelines:\n\n<guidelines>\n{guidelines_content}\n</guidelines>" if ctx.deps.guidelines else "") +
        f"This is the pipeline you are working on:\n\n{pipeline_desc}"
    )

    return full_system_prompt


class SweAgentV1(AgentV1[SWEDeps, str]):
    deps_class = SWEDeps
    deps: SWEDeps

    def __init__(self, deps: SWEDeps):
        super().__init__(deps, swe_agent)

    async def _setup_run(self) -> UUID:
        if self.deps.run_id is None:
            assert self.deps.run_name is not None, "Run name must be set for SWE runs"
            assert self.deps.kvasir_run_id is not None, "Kvasir run ID must be set for SWE runs"

            if self.deps.pipeline_id is None:
                # New pipeline for the ontology
                new_pipeline = await self.deps.ontology.insert_pipeline(
                    PipelineCreate(name=self.deps.run_name), edges=[])
                self.deps.pipeline_id = new_pipeline.id

            run = await self.deps.callbacks.create_swe_run(
                self.deps.user_id,
                self.deps.project_id,
                self.deps.kvasir_run_id,
                self.deps.pipeline_id,
                run_name=self.deps.run_name,
                initial_status="running"
            )
            self.deps.run_id = run.id

        await self.deps.callbacks.set_run_status(self.deps.user_id, self.deps.run_id, "running")
        return self.deps.run_id

    def update_time_limit(self, time_limit: int):
        self.deps.time_limit = time_limit

    def update_guidelines(self, guidelines: List[SUPPORTED_TASKS_LITERAL]):
        self.deps.guidelines = guidelines

    async def __call__(self, prompt: str, context: Optional[Context] = None) -> str:
        try:
            output = await super().__call__(prompt, context, describe_folder_structure=True)
            await self.deps.callbacks.save_result(self.deps.user_id, self.deps.run_id, output, "swe")

            await run_extraction_agent.kiq(
                f"The SWE agent just finished a run. Create new entities or update existing entities based on these results:\n\n{output}",
                user_id=self.deps.user_id,
                project_id=self.deps.project_id,
                package_name=self.deps.package_name,
                sandbox_type=self.deps.sandbox_type,
                bearer_token=self.deps.bearer_token,
                context=context
            )

            return output

        except Exception as e:
            await self.fail_run_if_exists(f"Error running SWE agent: {e}")
            raise e
