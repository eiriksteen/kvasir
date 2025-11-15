from pathlib import Path
from uuid import uuid4, UUID
from collections import OrderedDict
from dataclasses import dataclass, field
from taskiq import Context, TaskiqDepends
from typing import List, Dict, Tuple, Literal, Annotated

from kvasir_research.agents.abstract_agent import AbstractAgent
from kvasir_research.agents.kvasir_v1.orchestrator import orchestrator_agent, OrchestratorOutput, OrchestratorDeps
from kvasir_research.agents.kvasir_v1.swe import swe_agent, SWEDeps
from kvasir_research.agents.kvasir_v1.analysis import analysis_agent, AnalysisDeps
from kvasir_research.agents.kvasir_v1.knowledge_bank import SUPPORTED_TASKS_LITERAL
from kvasir_research.agents.kvasir_v1.callbacks import KvasirV1Callbacks
from kvasir_research.worker import broker


@dataclass
class AnalysisRun:
    deliverable_description: str
    run_id: str
    orchestrator_id: str
    project_id: str
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
    run_id: str
    orchestrator_id: str
    project_id: str
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


@broker.task
async def _run_swe(swe_run: SWERun, context: Annotated[Context, TaskiqDepends()]) -> str:
    callbacks: KvasirV1Callbacks = context.state.callbacks

    deps = SWEDeps(
        run_id=swe_run.run_id,
        orchestrator_id=UUID(swe_run.orchestrator_id),
        project_id=UUID(swe_run.project_id),
        package_name=swe_run.package_name,
        data_paths=swe_run.data_paths,
        injected_analyses=swe_run.injected_analyses,
        injected_swe_runs=swe_run.injected_swe_runs,
        read_only_paths=swe_run.read_only_paths,
        time_limit=swe_run.time_limit,
        guidelines=swe_run.guidelines,
        modified_files=swe_run.modified_files,
        sandbox_type=swe_run.sandbox_type
    )

    num_retries = 0
    try:
        await callbacks.save_swe_deps(deps.run_id, deps)
        while num_retries < swe_run.max_retries:
            try:
                swe_run_result = await swe_agent.run(
                    swe_run.deliverable_description,
                    deps=deps,
                    message_history=await callbacks.get_message_history(deps.run_id)
                )
            except Exception as e:
                num_retries += 1
                await callbacks.log(deps.orchestrator_id, f"SWE Agent [{deps.run_id}] failed to run: {e}, retrying... ({num_retries}/{swe_run.max_retries})")
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
            await kvasir_v1("Continue processing results from the queue.")

        return swe_run_result.output

    except (KeyboardInterrupt, Exception) as e:
        await callbacks.log(deps.orchestrator_id, f"SWE task failed or interrupted: {e}, cleaning up container")
        await deps.sandbox.delete_container_if_exists()
        raise


@broker.task
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
        orchestrator_id=UUID(analysis_run.orchestrator_id),
        project_id=UUID(analysis_run.project_id),
        package_name=analysis_run.package_name,
        data_paths=analysis_run.data_paths,
        injected_analyses=analysis_run.injected_analyses,
        time_limit=analysis_run.time_limit,
        guidelines=analysis_run.guidelines,
        notebook=notebook,
        sandbox_type=analysis_run.sandbox_type
    )

    num_retries = 0
    try:
        await callbacks.save_analysis_deps(deps.run_id, deps)
        while num_retries < analysis_run.max_retries:
            try:
                analysis_run_result = await analysis_agent.run(
                    analysis_run.deliverable_description,
                    deps=deps,
                    message_history=await callbacks.get_message_history(deps.run_id)
                )
            except Exception as e:
                num_retries += 1
                await callbacks.log(deps.orchestrator_id, f"Analysis Agent [{deps.run_id}] failed to run: {e}, retrying... ({num_retries}/{analysis_run.max_retries})")
                if num_retries == analysis_run.max_retries:
                    raise e
            else:
                break

        await callbacks.save_message_history(deps.run_id, analysis_run_result.all_messages())
        await deps.sandbox.write_file(
            str(Path("/app") / deps.package_name /
                "analysis" / f"{deps.run_id}.txt"),
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
            await kvasir_v1("Continue processing results from the queue.")

        return analysis_run_result.output

    except (KeyboardInterrupt, Exception) as e:
        await callbacks.log(deps.orchestrator_id, f"Analysis task failed or interrupted: {e}, cleaning up container")
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

    async def __call__(self, prompt: str) -> OrchestratorOutput:
        await self.callbacks.log(self.run_id, "Running orchestrator...")
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
            deps = await self.callbacks.load_orchestrator_deps(self.run_id)

        results_queue = await self.callbacks.get_results_queue(self.run_id)
        first = True
        outputs = []
        prompt = (
            f"This is the current state of the results queue:\n\n" +
            f"<results_queue>\n{'\n\n'.join(results_queue)}\n</results_queue>\n\n" +
            f"Now, take your actions based on the results. "
            f"The user prompt is:\n\n<user_prompt>\n{prompt}\n</user_prompt>"
        )

        await self.callbacks.log(self.run_id, f"Orchestrator prompt:\n\n{prompt}")
        await self.callbacks.log(self.run_id, f"Orchestrator message history size: {len(await self.callbacks.get_message_history(self.run_id))}")

        while results_queue or first:
            orchestrator_run = await orchestrator_agent.run(
                prompt,
                deps=deps,
                message_history=await self.callbacks.get_message_history(self.run_id)
            )

            await self.callbacks.save_message_history(self.run_id, orchestrator_run.all_messages())

            output: OrchestratorOutput = orchestrator_run.output
            outputs.append(output)

            await self.callbacks.log(self.run_id, f"Orchestrator output: {output}")

            if output.completed:
                await self.callbacks.set_orchestrator_run_status(self.run_id, "completed")
                await self.callbacks.log(self.run_id,
                                         f"Orchestrator completed, cleaning up container for project {deps.project_id}")
                await deps.sandbox.delete_container_if_exists()
                break

            for analysis_run_to_launch in output.analysis_runs_to_launch:
                full_run_id = f"{analysis_run_to_launch.run_id}-{uuid4()}"
                deps.launched_analysis_run_ids.append(full_run_id)

                await _run_analysis.kiq(
                    AnalysisRun(
                        deliverable_description=analysis_run_to_launch.deliverable_description,
                        run_id=full_run_id,
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
                saved_deps = await self.callbacks.load_analysis_deps(analysis_run_to_resume.run_id)
                # Use guidelines from resume request if provided, otherwise use saved deps
                guidelines = analysis_run_to_resume.guidelines if analysis_run_to_resume.guidelines else saved_deps.guidelines
                await _run_analysis.kiq(
                    AnalysisRun(
                        deliverable_description=analysis_run_to_resume.message,
                        run_id=analysis_run_to_resume.run_id,
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
                full_run_id = f"{swe_run_to_launch.run_id}-{uuid4()}"
                deps.launched_swe_run_ids.append(full_run_id)
                await _run_swe.kiq(
                    SWERun(
                        deliverable_description=swe_run_to_launch.deliverable_description,
                        run_id=full_run_id,
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
                saved_deps = await self.callbacks.load_swe_deps(swe_run_to_resume.run_id)
                # Use guidelines from resume request if provided, otherwise use saved deps
                guidelines = swe_run_to_resume.guidelines if swe_run_to_resume.guidelines else saved_deps.guidelines
                await _run_swe.kiq(
                    SWERun(
                        deliverable_description=swe_run_to_resume.message,
                        run_id=swe_run_to_resume.run_id,
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

        await self.callbacks.save_orchestrator_deps(self.run_id, deps)
        await self.callbacks.set_orchestrator_run_status(self.run_id, "waiting")
        return outputs
