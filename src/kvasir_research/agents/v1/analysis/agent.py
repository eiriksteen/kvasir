from pathlib import Path
from uuid import UUID
from typing import Optional, List
from pydantic_ai import Agent, RunContext
from pydantic_ai.models import ModelSettings

from kvasir_research.utils.agent_utils import get_model
from kvasir_research.agents.v1.history_processors import (
    keep_only_most_recent_analysis,
    keep_only_most_recent_project_description,
    keep_only_most_recent_folder_structure,
    keep_only_most_recent_entity_context
)
from kvasir_research.agents.v1.analysis.deps import AnalysisDeps
from kvasir_ontology.entities.analysis.data_model import AnalysisCreate
from kvasir_research.agents.v1.analysis.prompt import ANALYSIS_SYSTEM_PROMPT
from kvasir_research.agents.v1.kvasir.knowledge_bank import get_guidelines, SUPPORTED_TASKS_LITERAL
from kvasir_research.agents.v1.analysis.tools import analysis_toolset
from kvasir_research.agents.v1.analysis.output import submit_analysis_results
from kvasir_research.agents.v1.base_agent import AgentV1, Context
from kvasir_research.agents.v1.callbacks import KvasirV1Callbacks


model = get_model()


analysis_agent = Agent[AnalysisDeps, str](
    model,
    deps_type=AnalysisDeps,
    toolsets=[analysis_toolset],
    output_type=submit_analysis_results,
    retries=5,
    history_processors=[keep_only_most_recent_analysis,
                        keep_only_most_recent_project_description,
                        keep_only_most_recent_folder_structure,
                        keep_only_most_recent_entity_context],
    model_settings=ModelSettings(temperature=0)
)


@analysis_agent.system_prompt
async def analysis_system_prompt(ctx: RunContext[AnalysisDeps]) -> str:
    pyproject_str = ctx.deps.sandbox.get_pyproject_for_env_description()
    working_dir = await ctx.deps.sandbox.get_working_directory()
    guidelines_str = ""
    if ctx.deps.guidelines:
        guidelines_content = "\n\n".join(
            [get_guidelines(task) for task in ctx.deps.guidelines])
        guidelines_str = f"\n\n## Task-Specific Guidelines\n\n{guidelines_content}"

    assert ctx.deps.analysis is not None, "Analysis object must be set when the agent starts running"
    analysis_desc = await ctx.deps.ontology.describe_analysis(ctx.deps.analysis)

    full_system_prompt = (
        f"{ANALYSIS_SYSTEM_PROMPT}\n\n" +
        f"Data paths: {ctx.deps.data_paths}\n\n" +
        f"You environment is described by the following pyproject.toml:\n\n<pyproject>\n{pyproject_str}\n</pyproject>\n\n" +
        f"You are currently in the following working directory. For all paths, use this as the base path (absolute path needed):\n\n<working_dir>\n{working_dir}\n</working_dir>\n\n" +
        f"Here are the task-specific guidelines:\n\n<guidelines>\n{guidelines_str}\n</guidelines>" +
        f"This is the analysis you are working on:\n\n{analysis_desc}"
    )

    return full_system_prompt


class AnalysisAgentV1(AgentV1[AnalysisDeps, str]):
    deps_class = AnalysisDeps
    deps: AnalysisDeps

    def __init__(self, deps: AnalysisDeps):
        super().__init__(deps, analysis_agent)

    async def _setup_run(self) -> UUID:
        if self.deps.run_id is None:
            assert self.deps.run_name is not None, "Run name must be set for analysis runs"

            if self.deps.analysis_id is None:
                new_analysis = await self.deps.ontology.insert_analysis(AnalysisCreate(name=self.deps.run_name), edges=[])
                self.deps.analysis = new_analysis
                self.deps.analysis_id = new_analysis.id
            else:
                self.deps.analysis = await self.deps.ontology.analyses.get_analysis(self.deps.analysis_id)

            analysis_run = await self.deps.callbacks.create_analysis_run(
                self.deps.user_id, self.deps.project_id, self.deps.kvasir_run_id, self.deps.analysis_id, self.deps.run_name)
            self.deps.run_id = analysis_run.id

        await self.deps.callbacks.set_run_status(self.deps.user_id, self.deps.run_id, "running")
        return self.deps.run_id

    @classmethod
    async def load_deps(cls, user_id: UUID, run_id: UUID, callbacks: KvasirV1Callbacks, bearer_token: Optional[str] = None) -> AnalysisDeps:
        deps = await super().load_deps(user_id, run_id, callbacks, bearer_token)
        analysis_run = await deps.callbacks.get_analysis_run(user_id, run_id)
        analysis = await deps.ontology.analyses.get_analysis(analysis_run.analysis_id)
        deps.analysis = analysis
        return deps

    def update_time_limit(self, time_limit: int):
        self.deps.time_limit = time_limit

    def update_guidelines(self, guidelines: List[SUPPORTED_TASKS_LITERAL]):
        self.deps.guidelines = guidelines

    async def __call__(self, prompt: str, context: Optional[Context] = None) -> str:
        try:
            output = await super().__call__(prompt, context, describe_folder_structure=False)

            await self.deps.sandbox.write_file(
                str(Path("/app") / self.deps.package_name /
                    "analysis" / f"{self.deps.run_name}.txt"),
                output
            )

            await self.deps.callbacks.save_result(self.deps.user_id, self.deps.run_id, output, "analysis")
            return output

        except Exception as e:
            await self.fail_run_if_exists(f"Error running analysis agent: {e}")
            raise e
