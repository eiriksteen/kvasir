from uuid import UUID, uuid4
from typing import Literal, List, Optional, Dict
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
from kvasir_research.agents.v1.base_agent import BaseAgent
from kvasir_research.agents.v1.callbacks import KvasirV1Callbacks
from kvasir_research.agents.v1.data_model import RunCreate
from kvasir_ontology.ontology import Ontology


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


class SweAgentV1(BaseAgent):

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
        self._deps: Optional[SWEDeps] = None

    async def create_deps(
        self,
        kvasir_run_id: UUID,
        run_name: str,
        data_paths: List[str],
        injected_analyses: List[UUID],
        injected_swe_runs: List[UUID],
        read_only_paths: List[str],
        time_limit: int,
        guidelines: List[SUPPORTED_TASKS_LITERAL] = None,
    ) -> SWEDeps:
        if self.run_id is None:
            run_create = RunCreate(type="swe", project_id=self.project_id)
            self.run_id = (await self.callbacks.create_run(self.user_id, run_create)).id

        deps = SWEDeps(
            kvasir_run_id=kvasir_run_id,
            run_id=self.run_id,
            run_name=run_name,
            project_id=self.project_id,
            package_name=self.package_name,
            user_id=self.user_id,
            data_paths=data_paths,
            injected_analyses=injected_analyses,
            injected_swe_runs=injected_swe_runs,
            read_only_paths=read_only_paths,
            time_limit=time_limit,
            ontology=self.ontology,
            guidelines=guidelines or [],
            modified_files={},
            sandbox_type=self.sandbox_type,
            callbacks=self.callbacks,
            bearer_token=self.bearer_token,
        )
        self._deps = deps
        return deps

    async def load_deps_from_run(
        self,
        run_id: UUID,
        guidelines: Optional[List[SUPPORTED_TASKS_LITERAL]] = None,
        time_limit: Optional[int] = None,
    ) -> SWEDeps:
        try:
            deps_dict = await self.callbacks.load_deps(self.user_id, run_id, "swe")
        except (ValueError, RuntimeError):
            # Some callbacks raise exceptions when deps not found
            raise ValueError(f"SWE run {run_id} not found")

        if not deps_dict or "run_id" not in deps_dict:
            raise ValueError(f"SWE run {run_id} not found")

        deps = _swe_dict_to_deps(deps_dict, self.callbacks, self.ontology)

        # Apply overrides if provided
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
            if self._deps is None:
                if self.run_id is None:
                    raise ValueError(
                        "Must call create_deps() before starting a new agent run")
                else:
                    await self.load_deps_from_run(self.run_id, guidelines=guidelines, time_limit=time_limit)

            deps = self._deps

            # Apply overrides if provided
            if guidelines is not None:
                deps.guidelines = guidelines
            if time_limit is not None:
                deps.time_limit = time_limit

            message_history = None
            if self.run_id:
                message_history = await self.callbacks.get_message_history(self.user_id, self.run_id)

            await self.callbacks.set_run_status(self.user_id, self.run_id, "running")

            response = await swe_agent.run(
                prompt,
                deps=deps,
                message_history=message_history
            )

            await self.callbacks.save_message_history(self.user_id, self.run_id, response.all_messages())
            await self.callbacks.save_deps(self.user_id, self.run_id, _swe_deps_to_dict(deps), "swe")
            await self.callbacks.save_result(self.user_id, self.run_id, response.output, "swe")
            await self.callbacks.set_run_status(self.user_id, self.run_id, "completed")

            return response.output

        except Exception as e:
            if self.run_id:
                await self.callbacks.fail_run(self.user_id, self.run_id, f"Error running SWE agent: {e}")
            raise e


def _swe_deps_to_dict(deps: SWEDeps) -> Dict:
    # Convert UUIDs to strings for injected_analyses and injected_swe_runs
    injected_analyses_str = [str(aid) if isinstance(
        aid, UUID) else aid for aid in deps.injected_analyses]
    injected_swe_runs_str = [str(aid) if isinstance(
        aid, UUID) else aid for aid in deps.injected_swe_runs]

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
        "injected_swe_runs": injected_swe_runs_str,
        "read_only_paths": deps.read_only_paths,
        "time_limit": deps.time_limit,
        "guidelines": deps.guidelines,
        "modified_files": deps.modified_files,
        "sandbox_type": deps.sandbox_type,
    }


def _swe_dict_to_deps(deps_dict: Dict, callbacks: KvasirV1Callbacks, ontology: Ontology) -> SWEDeps:
    run_name = deps_dict.get("run_name", deps_dict.get("run_id"))
    try:
        run_uuid = UUID(deps_dict["run_id"])
    except Exception:
        # If previous versions stored run_name in run_id, generate a new UUID for run_id
        run_uuid = uuid4()

    # Convert string IDs to UUIDs for injected_analyses
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

    # Convert string IDs to UUIDs for injected_swe_runs
    injected_swe_runs_raw = deps_dict.get("injected_swe_runs", [])
    injected_swe_runs_uuids = []
    for aid in injected_swe_runs_raw:
        if isinstance(aid, str):
            try:
                injected_swe_runs_uuids.append(UUID(aid))
            except Exception as e:
                raise ValueError(
                    f"Invalid UUID string in injected_swe_runs: {aid}") from e
        elif isinstance(aid, UUID):
            injected_swe_runs_uuids.append(aid)
        else:
            raise TypeError(
                f"Invalid type in injected_swe_runs: {type(aid)}, expected str or UUID")

    deps = SWEDeps(
        run_id=run_uuid,
        run_name=run_name,
        project_id=UUID(deps_dict["project_id"]),
        package_name=deps_dict["package_name"],
        user_id=UUID(deps_dict["user_id"]) if deps_dict.get(
            "user_id") else None,
        data_paths=deps_dict["data_paths"],
        injected_analyses=injected_analyses_uuids,
        injected_swe_runs=injected_swe_runs_uuids,
        read_only_paths=deps_dict.get("read_only_paths", []),
        time_limit=deps_dict["time_limit"],
        ontology=ontology,
        guidelines=deps_dict.get("guidelines", []),
        modified_files=deps_dict.get("modified_files", {}),
        sandbox_type=deps_dict.get("sandbox_type", "local"),
        callbacks=callbacks,
        bearer_token=deps_dict.get("bearer_token"),
    )
    return deps
