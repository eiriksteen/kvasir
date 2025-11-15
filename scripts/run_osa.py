import asyncio
from uuid import uuid4, UUID
from typing import List, Dict, Tuple, Literal
from collections import OrderedDict
from pathlib import Path
from dataclasses import dataclass, field

from kvasir_research.osa.orchestrator import OrchestratorOutput, orchestrator_agent, OrchestratorDeps
from kvasir_research.osa.swe import swe_agent, SWEDeps
from kvasir_research.osa.analysis import analysis_agent, AnalysisDeps
from kvasir_research.osa.knowledge_bank import SUPPORTED_TASKS_LITERAL
from kvasir_research.utils.redis_utils import (
    get_message_history,
    save_message_history,
    get_results_queue,
    pop_result_from_queue,
    add_result_to_queue,
    save_deps,
    get_saved_deps,
    set_run_status,
    get_run_status,
    save_swe_result
)
from kvasir_research.sandbox.local import LocalSandbox
from kvasir_research.sandbox.modal import ModalSandbox
from kvasir_research.worker import broker, logger
from kvasir_research.secrets import PROJECTS_DIR


@dataclass
class AnalysisRun:
    deliverable_description: str
    run_id: str
    orchestrator_id: str
    project_path: str
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
    project_path: str
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


async def run_orchestrator(
        deliverable_description: str,
        deps: OrchestratorDeps) -> List[OrchestratorOutput]:

    logger.info("Running orchestrator...")

    run_id_str = str(deps.run_id)
    await set_run_status(run_id_str, "running")

    results_queue = await get_results_queue(run_id_str)
    first = True
    outputs = []
    prompt = (
        f"This is the current state of the results queue:\n\n" +
        f"<results_queue>\n{'\n\n'.join(results_queue)}\n</results_queue>\n\n" +
        f"Now, take your actions based on the results. "
        f"The deliverable description is:\n\n<deliverable_description>\n{deliverable_description}\n</deliverable_description>"
    )

    logger.info(f"Orchestrator prompt:\n\n{prompt}")
    logger.info(f"Orchestrator message history size: {len(await get_message_history(run_id_str))}")

    while results_queue or first:
        orchestrator_run = await orchestrator_agent.run(
            prompt,
            deps=deps,
            message_history=await get_message_history(run_id_str)
        )

        await save_message_history(run_id_str, orchestrator_run.all_messages())

        output: OrchestratorOutput = orchestrator_run.output
        outputs.append(output)

        logger.info(f"Orchestrator output: {output}")

        if output.completed:
            await set_run_status(run_id_str, "completed")
            logger.info(
                f"Orchestrator completed, cleaning up container for project {deps.project_id}")
            await deps.sandbox.delete_container_if_exists()
            break

        for analysis_run_to_launch in output.analysis_runs_to_launch:
            full_run_id = f"{analysis_run_to_launch.run_id}-{uuid4()}"
            deps.launched_analysis_run_ids.append(full_run_id)
            await run_analysis.kiq(AnalysisRun(
                deliverable_description=analysis_run_to_launch.deliverable_description,
                run_id=full_run_id,
                orchestrator_id=str(deps.run_id),
                data_paths=analysis_run_to_launch.data_paths,
                injected_analyses=analysis_run_to_launch.analyses_to_inject,
                project_path=str(deps.project_path),
                project_id=str(deps.project_id),
                package_name=deps.package_name,
                time_limit=analysis_run_to_launch.time_limit,
                guidelines=analysis_run_to_launch.guidelines,
                notebook={},
                sandbox_type=deps.sandbox_type
            ))

        for analysis_run_to_resume in output.analysis_runs_to_resume:
            saved_deps_dict = await get_saved_deps(analysis_run_to_resume.run_id)
            # Use guidelines from resume request if provided, otherwise use saved deps
            guidelines = analysis_run_to_resume.guidelines if analysis_run_to_resume.guidelines else saved_deps_dict.get(
                "guidelines", [])
            await run_analysis.kiq(AnalysisRun(
                deliverable_description=analysis_run_to_resume.message,
                run_id=analysis_run_to_resume.run_id,
                orchestrator_id=saved_deps_dict["orchestrator_id"],
                project_path=saved_deps_dict["project_path"],
                project_id=saved_deps_dict["project_id"],
                package_name=saved_deps_dict["package_name"],
                data_paths=saved_deps_dict["data_paths"],
                injected_analyses=saved_deps_dict["injected_analyses"],
                time_limit=analysis_run_to_resume.time_limit,
                guidelines=guidelines,
                notebook=saved_deps_dict.get("notebook", {}),
                sandbox_type=saved_deps_dict["sandbox_type"]
            ))

        for swe_run_to_launch in output.swe_runs_to_launch:
            full_run_id = f"{swe_run_to_launch.run_id}-{uuid4()}"
            deps.launched_swe_run_ids.append(full_run_id)
            await run_swe.kiq(SWERun(
                deliverable_description=swe_run_to_launch.deliverable_description,
                run_id=full_run_id,
                orchestrator_id=str(deps.run_id),
                data_paths=swe_run_to_launch.data_paths,
                injected_analyses=swe_run_to_launch.analyses_to_inject,
                injected_swe_runs=swe_run_to_launch.swe_runs_to_inject,
                read_only_paths=swe_run_to_launch.read_only_paths,
                project_path=str(deps.project_path),
                project_id=str(deps.project_id),
                package_name=deps.package_name,
                time_limit=swe_run_to_launch.time_limit,
                guidelines=swe_run_to_launch.guidelines,
                sandbox_type=deps.sandbox_type
            ))

        for swe_run_to_resume in output.swe_runs_to_resume:
            saved_deps_dict = await get_saved_deps(swe_run_to_resume.run_id)
            # Use guidelines from resume request if provided, otherwise use saved deps
            guidelines = swe_run_to_resume.guidelines if swe_run_to_resume.guidelines else saved_deps_dict.get(
                "guidelines", [])
            await run_swe.kiq(SWERun(
                deliverable_description=swe_run_to_resume.message,
                run_id=swe_run_to_resume.run_id,
                orchestrator_id=saved_deps_dict["orchestrator_id"],
                project_path=saved_deps_dict["project_path"],
                project_id=saved_deps_dict["project_id"],
                package_name=saved_deps_dict["package_name"],
                data_paths=saved_deps_dict["data_paths"],
                injected_analyses=saved_deps_dict["injected_analyses"],
                injected_swe_runs=saved_deps_dict.get("injected_swe_runs", []),
                read_only_paths=saved_deps_dict["read_only_paths"],
                time_limit=swe_run_to_resume.time_limit,
                guidelines=guidelines,
                modified_files=saved_deps_dict.get("modified_files", {}),
                sandbox_type=saved_deps_dict["sandbox_type"]
            ))

        await pop_result_from_queue(run_id_str)
        results_queue = await get_results_queue(run_id_str)
        first = False

        prompt = (
            "This is the current state of the results queue:\n\n" +
            f"<results_queue>{'\n\n'.join(results_queue)}</results_queue>\n\n" +
            "Now, take your actions based on the results. "
        )

    await save_deps(run_id_str, deps)
    await set_run_status(run_id_str, "waiting")
    return outputs


@broker.task
async def run_analysis(analysis_run: AnalysisRun) -> str:
    notebook = OrderedDict()
    for key, value in analysis_run.notebook.items():
        if isinstance(value, list):
            notebook[key] = tuple(value)
        else:
            notebook[key] = value

    deps = AnalysisDeps(
        run_id=analysis_run.run_id,
        orchestrator_id=UUID(analysis_run.orchestrator_id),
        project_path=Path(analysis_run.project_path),
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
        await save_deps(deps.run_id, deps)
        while num_retries < analysis_run.max_retries:
            try:
                analysis_run_result = await analysis_agent.run(
                    analysis_run.deliverable_description,
                    deps=deps,
                    message_history=await get_message_history(deps.run_id)
                )
            except Exception as e:
                num_retries += 1
                logger.warning(
                    f"Analysis Agent [{deps.run_id}] failed to run: {e}, retrying... ({num_retries}/{analysis_run.max_retries})")
                if num_retries == analysis_run.max_retries:
                    raise e
            else:
                break

        await save_message_history(deps.run_id, analysis_run_result.all_messages())
        await deps.sandbox.write_file(
            str(deps.project_path / "analysis" / f"{deps.run_id}.txt"),
            analysis_run_result.output
        )

        orchestrator_id_str = str(deps.orchestrator_id)
        await add_result_to_queue(orchestrator_id_str, analysis_run_result.output)

        if await get_run_status(orchestrator_id_str) == "waiting":
            orchestrator_deps_dict = await get_saved_deps(orchestrator_id_str)
            orchestrator_deps = _reconstruct_orchestrator_deps(
                orchestrator_deps_dict)
            await run_orchestrator("Continue processing results from the queue.", orchestrator_deps)

        return analysis_run_result.output

    except (KeyboardInterrupt, Exception) as e:
        logger.error(
            f"Analysis task failed or interrupted: {e}, cleaning up container")
        await deps.sandbox.delete_container_if_exists()
        raise


@broker.task
async def run_swe(swe_run: SWERun) -> str:
    deps = SWEDeps(
        run_id=swe_run.run_id,
        orchestrator_id=UUID(swe_run.orchestrator_id),
        project_path=Path(swe_run.project_path),
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
        await save_deps(deps.run_id, deps)
        while num_retries < swe_run.max_retries:
            try:
                swe_run_result = await swe_agent.run(
                    swe_run.deliverable_description,
                    deps=deps,
                    message_history=await get_message_history(deps.run_id)
                )
            except Exception as e:
                num_retries += 1
                logger.warning(
                    f"SWE Agent [{deps.run_id}] failed to run: {e}, retrying... ({num_retries}/{swe_run.max_retries})")
                if num_retries == swe_run.max_retries:
                    raise e
            else:
                break

        await save_message_history(deps.run_id, swe_run_result.all_messages())
        # Save SWE result to Redis for injection into other runs
        await save_swe_result(deps.run_id, swe_run_result.output)
        orchestrator_id_str = str(deps.orchestrator_id)
        await add_result_to_queue(orchestrator_id_str, swe_run_result.output)

        if await get_run_status(orchestrator_id_str) == "waiting":
            orchestrator_deps_dict = await get_saved_deps(orchestrator_id_str)
            orchestrator_deps = _reconstruct_orchestrator_deps(
                orchestrator_deps_dict)
            await run_orchestrator("Continue processing results from the queue.", orchestrator_deps)

        return swe_run_result.output

    except (KeyboardInterrupt, Exception) as e:
        logger.error(
            f"SWE task failed or interrupted: {e}, cleaning up container")
        await deps.sandbox.delete_container_if_exists()
        raise


def _reconstruct_orchestrator_deps(deps_dict: dict) -> OrchestratorDeps:
    """Reconstruct OrchestratorDeps from saved dict.
    The sandbox field is automatically recreated via __post_init__ based on sandbox_type and project_id."""
    deps_dict["run_id"] = UUID(deps_dict["run_id"])
    deps_dict["project_id"] = UUID(deps_dict["project_id"])
    deps_dict["project_path"] = Path(deps_dict["project_path"])
    deps_dict["package_name"] = deps_dict.get("package_name", "experiments")
    # sandbox is automatically created in __post_init__ based on sandbox_type and project_id
    return OrchestratorDeps(**deps_dict)


async def main(project_name: str, sandbox_type: Literal["local", "modal"] = "local") -> str:

    logger.info("Setting up project...")
    project_id = uuid4()
    run_id = uuid4()
    package_name = "experiments"
    if sandbox_type == "local":
        sandbox = LocalSandbox(project_id, package_name)
    elif sandbox_type == "modal":
        sandbox = ModalSandbox(project_id, package_name)

    try:
        project_path = await sandbox.setup_project(package_name)

        project_dir = PROJECTS_DIR / project_name
        with open(project_dir / "description.txt", "r") as f:
            deliverable_description = f.read()
            data_dir = project_dir / "data"

            data_structure = await sandbox.get_folder_structure(
                path=str(data_dir),
                n_levels=10,
                max_lines=200
            )

        orchestrator_deps = OrchestratorDeps(
            run_id=run_id,
            project_id=project_id,
            package_name=package_name,
            project_path=project_path,
            sandbox_type=sandbox_type
        )

        deliverable_description = (
            f"{deliverable_description}\n\n"
            f"The data directory structure:\n{data_structure}\n\n"
            f"The data is available at: {data_dir}"
        )
        logger.info(f"Deliverable description: {deliverable_description}")
        await run_orchestrator(deliverable_description, orchestrator_deps)

    except (KeyboardInterrupt, Exception) as e:
        logger.error(f"Error or interrupt occurred: {e}, cleaning up...")
        await sandbox.delete_container_if_exists()
        raise


if __name__ == "__main__":
    project_name = "weather_forecasting"
    asyncio.run(main(project_name, "modal"))
