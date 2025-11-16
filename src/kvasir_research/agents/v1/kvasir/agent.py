from pathlib import Path
from uuid import uuid4, UUID
from collections import OrderedDict
from dataclasses import dataclass, field
from taskiq import Context, TaskiqDepends
from typing import List, Dict, Tuple, Literal, Annotated, AsyncGenerator
from pydantic import ValidationError

from kvasir_research.agents.abstract_agent import AbstractAgent
from kvasir_research.agents.v1.kvasir.orchestrator import orchestrator_agent, OrchestratorOutput, OrchestratorDeps, OrchestratorOutputWithIds
from kvasir_research.agents.v1.kvasir.swe import swe_agent, SWEDeps
from kvasir_research.agents.v1.kvasir.analysis import analysis_agent, AnalysisDeps
from kvasir_research.agents.v1.kvasir.knowledge_bank import SUPPORTED_TASKS_LITERAL
from kvasir_research.agents.v1.kvasir.callbacks import KvasirV1Callbacks
from kvasir_research.agents.v1.broker import v1_broker


@dataclass
class AnalysisRun:
    deliverable_description: str
    run_id: UUID
    run_name: str
    orchestrator_id: UUID
    project_id: UUID
    package_name: str
    data_paths: List[str]
    injected_analyses: List[str]
    time_limit: int
    guidelines: List[SUPPORTED_TASKS_LITERAL] = field(default_factory=list)
    notebook: Dict[str, Tuple[str, str]] = field(default_factory=dict)
    max_retries: int = 2
    sandbox_type: Literal["local", "modal"] = "local"


@dataclass
class SWERun:
    deliverable_description: str
    run_id: UUID
    run_name: str
    orchestrator_id: UUID
    project_id: UUID
    package_name: str
    data_paths: List[str]
    injected_analyses: List[str]
    injected_swe_runs: List[str]
    read_only_paths: List[str]
    time_limit: int
    guidelines: List[SUPPORTED_TASKS_LITERAL] = field(default_factory=list)
    modified_files: Dict[str, str] = field(default_factory=dict)
    max_retries: int = 2
    sandbox_type: Literal["local", "modal"] = "local"


@v1_broker.task
async def _run_swe(swe_run: SWERun, context: Annotated[Context, TaskiqDepends()]) -> str:
    callbacks: KvasirV1Callbacks = context.state.callbacks

    deps = SWEDeps(
        run_id=swe_run.run_id,
        run_name=swe_run.run_name,
        orchestrator_id=swe_run.orchestrator_id,
        project_id=swe_run.project_id,
        package_name=swe_run.package_name,
        data_paths=swe_run.data_paths,
        injected_analyses=swe_run.injected_analyses,
        injected_swe_runs=swe_run.injected_swe_runs,
        read_only_paths=swe_run.read_only_paths,
        time_limit=swe_run.time_limit,
        guidelines=swe_run.guidelines,
        modified_files=swe_run.modified_files,
        sandbox_type=swe_run.sandbox_type,
        callbacks=callbacks
    )

    num_retries = 0
    try:
        await callbacks.save_swe_deps(deps.run_id, _swe_deps_to_dict(deps))
        while num_retries < swe_run.max_retries:
            try:
                swe_run_result = await swe_agent.run(
                    swe_run.deliverable_description,
                    deps=deps,
                    message_history=await callbacks.get_message_history(deps.run_id)
                )
            except Exception as e:
                num_retries += 1
                await callbacks.log(deps.orchestrator_id, f"SWE Agent [{deps.run_name}] failed to run: {e}, retrying... ({num_retries}/{swe_run.max_retries})", "error")
                if num_retries == swe_run.max_retries:
                    raise e
            else:
                break

        await callbacks.save_message_history(deps.run_id, swe_run_result.all_messages())
        # Save SWE result to Redis for injection into other runs
        await callbacks.save_swe_result(deps.run_id, swe_run_result.output)
        await callbacks.add_result_to_queue(deps.orchestrator_id, swe_run_result.output)

        if await callbacks.get_orchestrator_run_status(deps.orchestrator_id) == "waiting":
            kvasir_v1 = KvasirV1(
                run_id=deps.orchestrator_id,
                project_id=deps.project_id,
                package_name=swe_run.package_name,
                sandbox_type=swe_run.sandbox_type,
                callbacks=callbacks
            )
            async for _ in kvasir_v1("Continue processing results from the queue."):
                pass

        return swe_run_result.output

    except (KeyboardInterrupt, Exception) as e:
        await callbacks.log(deps.orchestrator_id, f"SWE task failed or interrupted: {e}, cleaning up container", "error")
        await deps.sandbox.delete_container_if_exists()
        raise


@v1_broker.task
async def _run_analysis(analysis_run: AnalysisRun, context: Annotated[Context, TaskiqDepends()]) -> str:
    callbacks: KvasirV1Callbacks = context.state.callbacks

    notebook = OrderedDict()
    for key, value in analysis_run.notebook.items():
        if isinstance(value, list):
            notebook[key] = tuple(value)
        else:
            notebook[key] = value

    deps = AnalysisDeps(
        run_id=analysis_run.run_id,
        run_name=analysis_run.run_name,
        orchestrator_id=analysis_run.orchestrator_id,
        project_id=analysis_run.project_id,
        package_name=analysis_run.package_name,
        data_paths=analysis_run.data_paths,
        injected_analyses=analysis_run.injected_analyses,
        time_limit=analysis_run.time_limit,
        guidelines=analysis_run.guidelines,
        notebook=notebook,
        sandbox_type=analysis_run.sandbox_type,
        callbacks=callbacks
    )

    num_retries = 0
    try:
        await callbacks.save_analysis_deps(deps.run_id, _analysis_deps_to_dict(deps))
        while num_retries < analysis_run.max_retries:
            try:
                analysis_run_result = await analysis_agent.run(
                    analysis_run.deliverable_description,
                    deps=deps,
                    message_history=await callbacks.get_message_history(deps.run_id)
                )
            except Exception as e:
                num_retries += 1
                await callbacks.log(deps.orchestrator_id, f"Analysis Agent [{deps.run_name}] failed to run: {e}, retrying... ({num_retries}/{analysis_run.max_retries})", "error")
                if num_retries == analysis_run.max_retries:
                    raise e
            else:
                break

        await callbacks.save_message_history(deps.run_id, analysis_run_result.all_messages())
        await deps.sandbox.write_file(
            str(Path("/app") / deps.package_name /
                "analysis" / f"{deps.run_name}.txt"),
            analysis_run_result.output
        )

        # Save analysis result to Redis for injection into other runs
        await callbacks.save_analysis_result(deps.run_id, analysis_run_result.output)
        await callbacks.add_result_to_queue(deps.orchestrator_id, analysis_run_result.output)

        if await callbacks.get_orchestrator_run_status(deps.orchestrator_id) == "waiting":
            kvasir_v1 = KvasirV1(
                run_id=deps.orchestrator_id,
                project_id=deps.project_id,
                package_name=analysis_run.package_name,
                sandbox_type=analysis_run.sandbox_type,
                callbacks=callbacks
            )
            async for _ in kvasir_v1("Continue processing results from the queue."):
                pass

        return analysis_run_result.output

    except (KeyboardInterrupt, Exception) as e:
        await callbacks.log(deps.orchestrator_id, f"Analysis task failed or interrupted: {e}, cleaning up container", "error")
        await deps.sandbox.delete_container_if_exists()
        raise


class KvasirV1(AbstractAgent):
    def __init__(
        self,
        run_id: UUID,
        project_id: UUID,
        package_name: str,
        sandbox_type: Literal["local", "modal"],
        callbacks: KvasirV1Callbacks
    ):
        super().__init__(run_id, project_id, package_name, sandbox_type, callbacks)
        self.callbacks = callbacks

    async def __call__(self, prompt: str) -> AsyncGenerator[Tuple[OrchestratorOutput, bool], None]:
        await self.callbacks.log(self.run_id, "Running orchestrator...", "tool_call")
        await self.callbacks.set_orchestrator_run_status(self.run_id, "running")
        is_new_run = await self.callbacks.check_orchestrator_run_exists(self.run_id)

        if is_new_run:
            await self.sandbox.setup_project(self.package_name)
            deps = OrchestratorDeps(
                run_id=self.run_id,
                project_id=self.project_id,
                package_name=self.package_name,
                sandbox_type=self.sandbox_type
            )
        else:
            deps_dict = await self.callbacks.load_orchestrator_deps(self.run_id)
            deps = _orchestrator_dict_to_deps(deps_dict, self.callbacks)

        results_queue = await self.callbacks.get_results_queue(self.run_id)
        first = True
        prompt = (
            f"This is the current state of the results queue:\n\n" +
            f"<results_queue>\n{'\n\n'.join(results_queue)}\n</results_queue>\n\n" +
            f"Now, take your actions based on the results. "
            f"The user prompt is:\n\n<user_prompt>\n{prompt}\n</user_prompt>"
        )

        await self.callbacks.log(self.run_id, f"Orchestrator prompt:\n\n{prompt}", "tool_call")
        await self.callbacks.log(self.run_id, f"Orchestrator message history size: {len(await self.callbacks.get_message_history(self.run_id))}", "tool_call")

        while results_queue or first:
            async with orchestrator_agent.run_stream(
                prompt,
                deps=deps,
                message_history=await self.callbacks.get_message_history(self.run_id)
            ) as orchestrator_run:
                async for message, last in orchestrator_run.stream_responses(debounce_by=0.01):
                    try:
                        output: OrchestratorOutputWithIds = await orchestrator_run.validate_response_output(
                            message,
                            allow_partial=not last
                        )
                        yield (output, last)
                    except ValidationError:
                        continue

            await self.callbacks.save_message_history(self.run_id, orchestrator_run.all_messages())
            await self.callbacks.log(self.run_id, f"Orchestrator output: {output}", "result")

            if output.completed:
                await self.callbacks.set_orchestrator_run_status(self.run_id, "completed")
                await self.callbacks.save_orchestrator_deps(self.run_id, _orchestrator_deps_to_dict(deps))
                await self.callbacks.log(self.run_id, f"Orchestrator completed, cleaning up container for project {deps.project_id}", "result")
                await deps.sandbox.delete_container_if_exists()
                break

            for analysis_run_to_launch in output.analysis_runs_to_launch:

                await _run_analysis.kiq(
                    AnalysisRun(
                        deliverable_description=analysis_run_to_launch.deliverable_description,
                        run_id=analysis_run_to_launch.run_id,
                        run_name=analysis_run_to_launch.run_name,
                        orchestrator_id=self.run_id,
                        data_paths=analysis_run_to_launch.data_paths,
                        injected_analyses=analysis_run_to_launch.analyses_to_inject,
                        project_id=self.project_id,
                        package_name=deps.package_name,
                        time_limit=analysis_run_to_launch.time_limit,
                        guidelines=analysis_run_to_launch.guidelines,
                        notebook={},
                        sandbox_type=deps.sandbox_type
                    )
                )

            for analysis_run_to_resume in output.analysis_runs_to_resume:
                saved_deps_dict = await self.callbacks.load_analysis_deps(analysis_run_to_resume.run_id)
                saved_deps = _analysis_dict_to_deps(
                    saved_deps_dict, self.callbacks)
                # Use guidelines from resume request if provided, otherwise use saved deps
                guidelines = analysis_run_to_resume.guidelines if analysis_run_to_resume.guidelines else saved_deps.guidelines
                await _run_analysis.kiq(
                    AnalysisRun(
                        deliverable_description=analysis_run_to_resume.message,
                        run_id=analysis_run_to_resume.run_id,
                        run_name=saved_deps.run_name,
                        orchestrator_id=saved_deps.orchestrator_id,
                        data_paths=saved_deps.data_paths,
                        injected_analyses=saved_deps.injected_analyses,
                        project_id=saved_deps.project_id,
                        package_name=saved_deps.package_name,
                        time_limit=analysis_run_to_resume.time_limit,
                        guidelines=guidelines,
                        notebook=saved_deps.notebook,
                        sandbox_type=saved_deps.sandbox_type
                    )
                )

            for swe_run_to_launch in output.swe_runs_to_launch:
                await _run_swe.kiq(
                    SWERun(
                        deliverable_description=swe_run_to_launch.deliverable_description,
                        run_id=swe_run_to_launch.run_id,
                        run_name=swe_run_to_launch.run_name,
                        orchestrator_id=self.run_id,
                        data_paths=swe_run_to_launch.data_paths,
                        injected_analyses=swe_run_to_launch.analyses_to_inject,
                        injected_swe_runs=swe_run_to_launch.swe_runs_to_inject,
                        read_only_paths=swe_run_to_launch.read_only_paths,
                        project_id=self.project_id,
                        package_name=deps.package_name,
                        time_limit=swe_run_to_launch.time_limit,
                        guidelines=swe_run_to_launch.guidelines,
                        sandbox_type=deps.sandbox_type
                    )
                )

            for swe_run_to_resume in output.swe_runs_to_resume:
                saved_deps_dict = await self.callbacks.load_swe_deps(swe_run_to_resume.run_id)
                saved_deps = _swe_dict_to_deps(saved_deps_dict, self.callbacks)
                # Use guidelines from resume request if provided, otherwise use saved deps
                guidelines = swe_run_to_resume.guidelines if swe_run_to_resume.guidelines else saved_deps.guidelines
                await _run_swe.kiq(
                    SWERun(
                        deliverable_description=swe_run_to_resume.message,
                        run_id=swe_run_to_resume.run_id,
                        run_name=saved_deps.run_name,
                        orchestrator_id=saved_deps.orchestrator_id,
                        project_id=saved_deps.project_id,
                        package_name=saved_deps.package_name,
                        data_paths=saved_deps.data_paths,
                        injected_analyses=saved_deps.injected_analyses,
                        injected_swe_runs=saved_deps.injected_swe_runs,
                        read_only_paths=saved_deps.read_only_paths,
                        time_limit=swe_run_to_resume.time_limit,
                        guidelines=guidelines,
                        modified_files=saved_deps.modified_files,
                        sandbox_type=saved_deps.sandbox_type
                    )
                )

            await self.callbacks.pop_result_from_queue(self.run_id)
            results_queue = await self.callbacks.get_results_queue(self.run_id)
            first = False

            prompt = (
                "This is the current state of the results queue:\n\n" +
                f"<results_queue>{'\n\n'.join(results_queue)}</results_queue>\n\n" +
                "Now, take your actions based on the results. "
            )

            await self.callbacks.save_orchestrator_deps(self.run_id, _orchestrator_deps_to_dict(deps))
            await self.callbacks.set_orchestrator_run_status(self.run_id, "waiting")


###


def _orchestrator_deps_to_dict(deps: OrchestratorDeps) -> Dict:
    return {
        "run_id": str(deps.run_id),
        "project_id": str(deps.project_id),
        "package_name": deps.package_name,
        "launched_analysis_run_ids": [str(x) for x in deps.launched_analysis_run_ids],
        "launched_swe_run_ids": [str(x) for x in deps.launched_swe_run_ids],
        "sandbox_type": deps.sandbox_type,
    }


def _orchestrator_dict_to_deps(deps_dict: Dict, callbacks: KvasirV1Callbacks) -> OrchestratorDeps:
    deps = OrchestratorDeps(
        run_id=UUID(deps_dict["run_id"]),
        project_id=UUID(deps_dict["project_id"]),
        package_name=deps_dict["package_name"],
        launched_analysis_run_ids=[UUID(x) for x in deps_dict.get(
            "launched_analysis_run_ids", [])],
        launched_swe_run_ids=[UUID(x) for x in deps_dict.get(
            "launched_swe_run_ids", [])],
        sandbox_type=deps_dict.get("sandbox_type", "local"),
    )
    return deps


def _swe_deps_to_dict(deps: SWEDeps) -> Dict:
    return {
        "run_id": str(deps.run_id),
        "run_name": deps.run_name,
        "orchestrator_id": str(deps.orchestrator_id),
        "project_id": str(deps.project_id),
        "package_name": deps.package_name,
        "data_paths": deps.data_paths,
        "injected_analyses": deps.injected_analyses,
        "injected_swe_runs": deps.injected_swe_runs,
        "read_only_paths": deps.read_only_paths,
        "time_limit": deps.time_limit,
        "guidelines": deps.guidelines,
        "modified_files": deps.modified_files,
        "sandbox_type": deps.sandbox_type,
    }


def _swe_dict_to_deps(deps_dict: Dict, callbacks: KvasirV1Callbacks) -> SWEDeps:
    run_uuid = UUID(deps_dict["run_id"])
    run_name = deps_dict["run_name"]

    deps = SWEDeps(
        run_id=run_uuid,
        run_name=run_name,
        orchestrator_id=UUID(deps_dict["orchestrator_id"]),
        project_id=UUID(deps_dict["project_id"]),
        package_name=deps_dict["package_name"],
        data_paths=deps_dict["data_paths"],
        injected_analyses=deps_dict.get("injected_analyses", []),
        injected_swe_runs=deps_dict.get("injected_swe_runs", []),
        read_only_paths=deps_dict.get("read_only_paths", []),
        time_limit=deps_dict["time_limit"],
        guidelines=deps_dict.get("guidelines", []),
        modified_files=deps_dict.get("modified_files", {}),
        sandbox_type=deps_dict.get("sandbox_type", "local"),
        callbacks=callbacks,
    )
    return deps


def _analysis_deps_to_dict(deps: AnalysisDeps) -> Dict:
    notebook_dict = {}
    for key, value in deps.notebook.items():
        if isinstance(value, tuple):
            notebook_dict[key] = list(value)
        else:
            notebook_dict[key] = value

    return {
        "run_id": str(deps.run_id),
        "run_name": deps.run_name,
        "orchestrator_id": str(deps.orchestrator_id),
        "project_id": str(deps.project_id),
        "package_name": deps.package_name,
        "data_paths": deps.data_paths,
        "injected_analyses": deps.injected_analyses,
        "time_limit": deps.time_limit,
        "notebook": notebook_dict,
        "guidelines": deps.guidelines,
        "sandbox_type": deps.sandbox_type,
    }


def _analysis_dict_to_deps(deps_dict: Dict, callbacks: KvasirV1Callbacks) -> AnalysisDeps:
    notebook_raw = deps_dict.get("notebook", {})
    notebook = OrderedDict()
    for k, v in notebook_raw.items():
        if isinstance(v, list):
            notebook[k] = tuple(v)
        else:
            notebook[k] = v

    # Backward compatibility: handle cases where run_name is missing or run_id stored as name
    run_name = deps_dict.get("run_name", deps_dict.get("run_id"))
    try:
        run_uuid = UUID(deps_dict["run_id"])
    except Exception:
        # If previous versions stored run_name in run_id, generate a new UUID for run_id
        run_uuid = uuid4()

    deps = AnalysisDeps(
        run_id=run_uuid,
        run_name=run_name,
        orchestrator_id=UUID(deps_dict["orchestrator_id"]),
        project_id=UUID(deps_dict["project_id"]),
        package_name=deps_dict["package_name"],
        data_paths=deps_dict["data_paths"],
        injected_analyses=deps_dict.get("injected_analyses", []),
        time_limit=deps_dict["time_limit"],
        notebook=notebook,
        guidelines=deps_dict.get("guidelines", []),
        sandbox_type=deps_dict.get("sandbox_type", "local"),
        callbacks=callbacks,
    )
    return deps
