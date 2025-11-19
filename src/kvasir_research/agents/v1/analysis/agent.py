from pathlib import Path
from uuid import UUID, uuid4
from typing import Literal, List, OrderedDict, Optional, Dict
from pydantic_ai import Agent, RunContext
from pydantic_ai.models import ModelSettings

from kvasir_research.utils.agent_utils import get_model
from kvasir_research.history_processors import keep_only_most_recent_notebook
from kvasir_research.agents.v1.analysis.deps import AnalysisDeps
from kvasir_ontology.entities.analysis.data_model import AnalysisCreate
from kvasir_research.agents.v1.analysis.prompt import ANALYSIS_SYSTEM_PROMPT
from kvasir_research.agents.v1.kvasir.knowledge_bank import get_guidelines, SUPPORTED_TASKS_LITERAL
from kvasir_research.agents.v1.analysis.tools import analysis_toolset
from kvasir_research.agents.v1.analysis.output import submit_analysis_results
from kvasir_research.agents.v1.base_agent import BaseAgent
from kvasir_research.agents.v1.callbacks import KvasirV1Callbacks
from kvasir_research.agents.v1.data_model import RunCreate
from kvasir_ontology.ontology import Ontology


model = get_model()


analysis_agent = Agent[AnalysisDeps, str](
    model,
    deps_type=AnalysisDeps,
    toolsets=[analysis_toolset],
    output_type=submit_analysis_results,
    retries=5,
    history_processors=[keep_only_most_recent_notebook],
    model_settings=ModelSettings(temperature=0)
)


@analysis_agent.system_prompt
async def analysis_system_prompt(ctx: RunContext[AnalysisDeps]) -> str:
    injected_analyses_str = "\n\n".join([await ctx.deps.callbacks.get_result(ctx.deps.user_id, analysis_run_id, "analysis") for analysis_run_id in ctx.deps.injected_analyses])
    pyproject_str = ctx.deps.sandbox.get_pyproject_for_env_description()

    guidelines_str = ""
    if ctx.deps.guidelines:
        guidelines_content = "\n\n".join(
            [get_guidelines(task) for task in ctx.deps.guidelines])
        guidelines_str = f"\n\n## Task-Specific Guidelines\n\n{guidelines_content}"

    full_system_prompt = (
        f"{ANALYSIS_SYSTEM_PROMPT}\n\n" +
        f"Data paths: {ctx.deps.data_paths}\n\n" +
        f"You environment is described by the following pyproject.toml:\n\n<pyproject>\n{pyproject_str}\n</pyproject>\n\n" +
        f"Here are results from previous analyses:\n\n<analyses>\n{injected_analyses_str}\n</analyses>\n\n" +
        f"Here are the task-specific guidelines:\n\n<guidelines>\n{guidelines_str}\n</guidelines>"
    )

    return full_system_prompt


class AnalysisAgentV1(BaseAgent):

    def __init__(
        self,
        user_id: UUID,
        project_id: UUID,
        package_name: str,
        sandbox_type: Literal["local", "modal"],
        callbacks: KvasirV1Callbacks,
        bearer_token: Optional[str] = None,
        run_id: Optional[UUID] = None
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
        self.callbacks = callbacks
        self._deps: Optional[AnalysisDeps] = None

    async def create_deps(
        self,
        kvasir_run_id: UUID,
        run_name: str,
        data_paths: List[str],
        injected_analyses: List[UUID],
        time_limit: int,
        guidelines: List[SUPPORTED_TASKS_LITERAL] = None,
    ) -> AnalysisDeps:
        if self.run_id is None:
            run_create = RunCreate(type="analysis", project_id=self.project_id)
            self.run_id = (await self.callbacks.create_run(self.user_id, run_create)).id

        deps = AnalysisDeps(
            kvasir_run_id=kvasir_run_id,
            run_id=self.run_id,
            run_name=run_name,
            project_id=self.project_id,
            package_name=self.package_name,
            data_paths=data_paths,
            injected_analyses=injected_analyses,
            time_limit=time_limit,
            guidelines=guidelines or [],
            notebook=OrderedDict(),
            ontology=self.ontology,
            sandbox_type=self.sandbox_type,
            callbacks=self.callbacks,
        )
        self._deps = deps
        return deps

    async def load_deps_from_run(
        self,
        run_id: UUID,
        guidelines: Optional[List[SUPPORTED_TASKS_LITERAL]] = None,
        time_limit: Optional[int] = None,
    ) -> AnalysisDeps:
        try:
            deps_dict = await self.callbacks.load_deps(self.user_id, run_id, "analysis")
        except (ValueError, RuntimeError):
            raise ValueError(f"Analysis run {run_id} not found")

        if not deps_dict or "run_id" not in deps_dict:
            raise ValueError(f"Analysis run {run_id} not found")

        deps = _analysis_dict_to_deps(deps_dict, self.callbacks, self.ontology)

        if guidelines is not None:
            deps.guidelines = guidelines
        if time_limit is not None:
            deps.time_limit = time_limit

        self.run_id = run_id
        self._deps = deps
        return deps

    async def __call__(
        self,
        prompt: str,
        guidelines: Optional[List[SUPPORTED_TASKS_LITERAL]] = None,
        time_limit: Optional[int] = None,
    ) -> str:
        try:
            if self.run_id is None:
                self.analysis = await self.ontology.insert_analysis(AnalysisCreate(
                    name=self._deps.run_name,
                    description=None,
                    code_cells_create=[],
                    markdown_cells_create=[]
                ), edges=[])
                self.run = await self.callbacks.create_analysis_run(self.user_id, self.project_id, self._deps.kvasir_run_id, self.analysis.id, self._deps.run_name)
            else:
                self.run = await self.callbacks.get_analysis_run(self.user_id, self.run_id)
                self.analysis = await self.ontology.analyses.get_analysis(self.run.analysis_id)

            deps = self._deps

            if guidelines is not None:
                deps.guidelines = guidelines
            if time_limit is not None:
                deps.time_limit = time_limit

            message_history = None
            if self.run_id:
                message_history = await self.callbacks.get_message_history(self.user_id, self.run_id)

            await self.callbacks.set_run_status(self.user_id, self.run_id, "running")

            response = await analysis_agent.run(
                prompt,
                deps=deps,
                message_history=message_history
            )

            await deps.sandbox.write_file(
                str(Path("/app") / deps.package_name /
                    "analysis" / f"{deps.run_name}.txt"),
                response.output
            )

            await self.callbacks.save_message_history(self.user_id, self.run_id, response.all_messages())
            await self.callbacks.save_deps(self.user_id, self.run_id, _analysis_deps_to_dict(deps), "analysis")
            await self.callbacks.save_result(self.user_id, self.run_id, response.output, "analysis")
            await self.callbacks.set_run_status(self.user_id, self.run_id, "completed")

            return response.output

        except Exception as e:
            if self.run_id:
                await self.callbacks.fail_run(self.user_id, self.run_id, f"Error running analysis agent: {e}")
            raise e


def _analysis_deps_to_dict(deps: AnalysisDeps) -> Dict:
    notebook_dict = {}
    for key, value in deps.notebook.items():
        if isinstance(value, tuple):
            notebook_dict[key] = list(value)
        else:
            notebook_dict[key] = value

    # Convert UUIDs to strings for injected_analyses
    injected_analyses_str = [str(aid) if isinstance(
        aid, UUID) else aid for aid in deps.injected_analyses]

    return {
        "run_id": str(deps.run_id),
        "kvasir_run_id": str(deps.kvasir_run_id),
        "run_name": deps.run_name,
        "project_id": str(deps.project_id),
        "package_name": deps.package_name,
        "user_id": str(deps.user_id) if deps.user_id else None,
        "bearer_token": deps.bearer_token,
        "data_paths": deps.data_paths,
        "injected_analyses": injected_analyses_str,
        "time_limit": deps.time_limit,
        "notebook": notebook_dict,
        "guidelines": deps.guidelines,
        "sandbox_type": deps.sandbox_type,
    }


def _analysis_dict_to_deps(deps_dict: Dict, callbacks: KvasirV1Callbacks, ontology: Ontology) -> AnalysisDeps:
    notebook_raw = deps_dict.get("notebook", {})
    notebook = OrderedDict()
    for k, v in notebook_raw.items():
        if isinstance(v, list):
            notebook[k] = tuple(v)
        else:
            notebook[k] = v

    run_name = deps_dict.get("run_name", deps_dict.get("run_id"))
    try:
        run_uuid = UUID(deps_dict["run_id"])
    except Exception:
        run_uuid = uuid4()

    injected_analyses_raw = deps_dict.get("injected_analyses", [])
    injected_analyses_uuids = []
    for aid in injected_analyses_raw:
        if isinstance(aid, str):
            try:
                injected_analyses_uuids.append(UUID(aid))
            except Exception as e:
                raise ValueError(
                    f"Invalid UUID string in injected_analyses: {aid}") from e
        elif isinstance(aid, UUID):
            injected_analyses_uuids.append(aid)
        else:
            raise TypeError(
                f"Invalid type in injected_analyses: {type(aid)}, expected str or UUID")

    deps = AnalysisDeps(
        run_id=run_uuid,
        kvasir_run_id=UUID(deps_dict["kvasir_run_id"]),
        run_name=run_name,
        project_id=UUID(deps_dict["project_id"]),
        package_name=deps_dict["package_name"],
        user_id=UUID(deps_dict["user_id"]) if deps_dict.get(
            "user_id") else None,
        data_paths=deps_dict["data_paths"],
        injected_analyses=injected_analyses_uuids,
        time_limit=deps_dict["time_limit"],
        notebook=notebook,
        ontology=ontology,
        guidelines=deps_dict.get("guidelines", []),
        sandbox_type=deps_dict.get("sandbox_type", "local"),
        callbacks=callbacks,
        bearer_token=deps_dict.get("bearer_token")
    )
    return deps
