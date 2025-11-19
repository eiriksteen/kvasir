from uuid import UUID
from typing import List, Optional
from typing_extensions import Self
from pydantic_ai import Agent, RunContext
from pydantic_ai.models import ModelSettings

from kvasir_research.utils.agent_utils import get_model
from kvasir_research.history_processors import keep_only_most_recent_script
from kvasir_research.agents.v1.swe.deps import SWEDeps
from kvasir_research.agents.v1.swe.prompt import SWE_SYSTEM_PROMPT
from kvasir_research.agents.v1.kvasir.knowledge_bank import get_guidelines, SUPPORTED_TASKS_LITERAL
from kvasir_research.agents.v1.shared_tools import navigation_toolset, knowledge_bank_toolset
from kvasir_research.agents.v1.swe.tools import swe_toolset
from kvasir_research.agents.v1.swe.output import submit_implementation_results, submit_message_to_orchestrator
from kvasir_research.agents.v1.base_agent import AgentV1
from kvasir_research.agents.v1.callbacks import KvasirV1Callbacks


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
    history_processors=[keep_only_most_recent_script],
    model_settings=ModelSettings(temperature=0)
)


@swe_agent.system_prompt
async def swe_system_prompt(ctx: RunContext[SWEDeps]) -> str:
    ls, ls_err = await ctx.deps.sandbox.list_directory_contents()

    if ls_err:
        raise RuntimeError(
            f"Failed to list working directory contents: {ls_err}")

    current_wd = f"ls out:\n{ls}\n\n"
    folder_structure = await ctx.deps.sandbox.get_folder_structure()
    env_description = ctx.deps.sandbox.get_pyproject_for_env_description()

    injected_analyses_str = "\n\n".join([await ctx.deps.callbacks.get_result(ctx.deps.user_id, analysis_run_id, "analysis") for analysis_run_id in ctx.deps.injected_analyses])
    injected_swe_runs_str = "\n\n".join([await ctx.deps.callbacks.get_result(ctx.deps.user_id, swe_run_id, "swe") for swe_run_id in ctx.deps.injected_swe_runs])

    guidelines_str = ""
    if ctx.deps.guidelines:
        guidelines_content = "\n\n".join(
            [get_guidelines(task) for task in ctx.deps.guidelines])
        guidelines_str = f"\n\n## Task-Specific Guidelines\n\n{guidelines_content}"

    full_system_prompt = (
        f"{SWE_SYSTEM_PROMPT}\n\n" +
        f"Package name: {ctx.deps.package_name}\n\n" +
        f"Current working directory: {current_wd}\n\n" +
        f"Folder structure: {folder_structure}\n\n" +
        f"Data paths to use: {ctx.deps.data_paths}\n\n" +
        f"Read only paths: {ctx.deps.read_only_paths}\n\n" +
        f"You environment is described by the following pyproject.toml:\n\n<pyproject>\n{env_description}\n</pyproject>\n\n" +
        f"Here are results from previous analyses:\n\n<analyses>\n{injected_analyses_str}\n</analyses>\n\n" +
        f"Here are results from previous SWE runs:\n\n<swe_runs>\n{injected_swe_runs_str}\n</swe_runs>" +
        guidelines_str
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
            run = await self.deps.callbacks.create_swe_run(
                self.deps.user_id,
                self.deps.project_id,
                self.deps.kvasir_run_id,
                run_name=self.deps.run_name,
                initial_status="running"
            )
            self.deps.run_id = run.id

        await self.deps.callbacks.set_run_status(self.deps.user_id, self.deps.run_id, "running")
        return self.deps.run_id

    @classmethod
    async def from_run(cls, user_id: UUID, run_id: UUID, callbacks: KvasirV1Callbacks, bearer_token: Optional[str] = None) -> Self:
        return await super().from_run(user_id, run_id, callbacks, bearer_token)

    def update_time_limit(self, time_limit: int):
        self.deps.time_limit = time_limit

    def update_guidelines(self, guidelines: List[SUPPORTED_TASKS_LITERAL]):
        self.deps.guidelines = guidelines

    async def __call__(self, prompt: str) -> str:
        try:
            await self._setup_run()
            output = await self._run_agent(prompt)
            await self.finish_run("SWE run completed")
            await self.deps.callbacks.save_result(self.deps.user_id, self.deps.run_id, output, "swe")
            return output

        except Exception as e:
            await self.fail_run_if_exists(f"Error running SWE agent: {e}")
            raise e
