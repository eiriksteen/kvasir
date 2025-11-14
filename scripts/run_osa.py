import asyncio
from uuid import uuid4, UUID
from typing import List
from collections import OrderedDict
from pathlib import Path
from time import time

from kvasir_research.osa.orchestrator import OrchestratorOutput, orchestrator_agent, OrchestratorDeps
from kvasir_research.osa.swe import swe_agent, SWEDeps
from kvasir_research.osa.analysis import analysis_agent, AnalysisDeps
from kvasir_research.utils.redis_utils import (
    get_message_history,
    save_message_history,
    get_results_queue,
    pop_result_from_queue,
    add_result_to_queue,
    save_deps,
    get_saved_deps,
    set_run_status,
    get_run_status
)
from kvasir_research.utils.docker_utils import (
    create_project_container_if_not_exists,
    copy_file_or_directory_to_container,
    delete_project_container_if_exists,
    write_file_to_container,
    install_package_after_start
)
from kvasir_research.utils.file_utils import get_folder_structure_description
from kvasir_research.worker import broker, logger
from kvasir_research.secrets import PROJECTS_DIR


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
        f"The deliverable description is:\n\n<deliverable_description>{deliverable_description}</deliverable_description>"
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
            # Cleanup container on completion
            logger.info(
                f"Orchestrator completed, cleaning up container for project {deps.project_id}")
            delete_project_container_if_exists(deps.project_id)
            break

        for analysis_run_to_launch in output.analysis_runs_to_launch:
            full_run_id = f"{analysis_run_to_launch.run_id}-{uuid4()}"
            deps.launched_analysis_run_ids.append(full_run_id)
            await run_analysis.kiq(analysis_run_to_launch.deliverable_description, AnalysisDeps(
                run_id=full_run_id,
                container_name=deps.container_name,
                orchestrator_id=deps.run_id,
                data_paths=analysis_run_to_launch.data_paths,
                injected_analyses=analysis_run_to_launch.analyses_to_inject,
                project_path=deps.project_path,
                project_id=deps.project_id,
                time_limit=analysis_run_to_launch.time_limit,
                notebook=OrderedDict()
            ))

        for analysis_run_to_resume in output.analysis_runs_to_resume:
            saved_deps_dict = await get_saved_deps(analysis_run_to_resume.run_id)
            saved_deps = _reconstruct_analysis_deps(saved_deps_dict)
            saved_deps.time_limit = analysis_run_to_resume.time_limit
            await run_analysis.kiq(analysis_run_to_resume.message, saved_deps)

        for swe_run_to_launch in output.swe_runs_to_launch:
            full_run_id = f"{swe_run_to_launch.run_id}-{uuid4()}"
            deps.launched_swe_run_ids.append(full_run_id)
            await run_swe.kiq(swe_run_to_launch.deliverable_description, SWEDeps(
                run_id=full_run_id,
                container_name=deps.container_name,
                orchestrator_id=deps.run_id,
                data_paths=swe_run_to_launch.data_paths,
                injected_analyses=swe_run_to_launch.analyses_to_inject,
                read_only_paths=swe_run_to_launch.read_only_paths,
                project_path=deps.project_path,
                project_id=deps.project_id,
                time_limit=swe_run_to_launch.time_limit
            ))

        for swe_run_to_resume in output.swe_runs_to_resume:
            saved_deps_dict = await get_saved_deps(swe_run_to_resume.run_id)
            saved_deps = _reconstruct_swe_deps(saved_deps_dict)
            saved_deps.time_limit = swe_run_to_resume.time_limit
            await run_swe.kiq(swe_run_to_resume.message, saved_deps)

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
async def run_analysis(
        deliverable_description: str,
        deps: AnalysisDeps,
        max_retries: int = 2) -> str:

    num_retries = 0
    try:
        await save_deps(deps.run_id, deps)
        while num_retries < max_retries:
            try:
                analysis_run = await analysis_agent.run(
                    deliverable_description,
                    deps=deps,
                    message_history=await get_message_history(deps.run_id)
                )
            except Exception as e:
                num_retries += 1
                logger.warning(
                    f"Analysis Agent [{deps.run_id}] failed to run: {e}, retrying... ({num_retries}/{max_retries})")
                if num_retries == max_retries:
                    raise e
            else:
                break

        await save_message_history(deps.run_id, analysis_run.all_messages())
        await write_file_to_container(
            deps.project_path / "analysis" / f"{deps.run_id}.txt",
            analysis_run.output,
            deps.container_name
        )

        orchestrator_id_str = str(deps.orchestrator_id)
        await add_result_to_queue(orchestrator_id_str, analysis_run.output)

        if await get_run_status(orchestrator_id_str) == "waiting":
            orchestrator_deps_dict = await get_saved_deps(orchestrator_id_str)
            orchestrator_deps = _reconstruct_orchestrator_deps(
                orchestrator_deps_dict)
            await run_orchestrator("Continue processing results from the queue.", orchestrator_deps)

        return analysis_run.output

    except (KeyboardInterrupt, Exception) as e:
        logger.error(
            f"Analysis task failed or interrupted: {e}, cleaning up container")
        delete_project_container_if_exists(deps.project_id)
        raise


@broker.task
async def run_swe(
        deliverable_description: str,
        deps: SWEDeps,
        max_retries: int = 2
) -> str:

    num_retries = 0
    try:
        await save_deps(deps.run_id, deps)
        while num_retries < max_retries:
            try:
                swe_run = await swe_agent.run(
                    deliverable_description,
                    deps=deps,
                    message_history=await get_message_history(deps.run_id)
                )
            except Exception as e:
                num_retries += 1
                logger.warning(
                    f"SWE Agent [{deps.run_id}] failed to run: {e}, retrying... ({num_retries}/{max_retries})")
                if num_retries == max_retries:
                    raise e
            else:
                break

        await save_message_history(deps.run_id, swe_run.all_messages())
        orchestrator_id_str = str(deps.orchestrator_id)
        await add_result_to_queue(orchestrator_id_str, swe_run.output)

        if await get_run_status(orchestrator_id_str) == "waiting":
            orchestrator_deps_dict = await get_saved_deps(orchestrator_id_str)
            orchestrator_deps = _reconstruct_orchestrator_deps(
                orchestrator_deps_dict)
            await run_orchestrator("Continue processing results from the queue.", orchestrator_deps)

        return swe_run.output

    except (KeyboardInterrupt, Exception) as e:
        logger.error(
            f"SWE task failed or interrupted: {e}, cleaning up container")
        delete_project_container_if_exists(deps.project_id)
        raise


def _reconstruct_analysis_deps(deps_dict: dict) -> AnalysisDeps:
    deps_dict["orchestrator_id"] = UUID(deps_dict["orchestrator_id"])
    deps_dict["project_path"] = Path(deps_dict["project_path"])
    deps_dict["project_id"] = UUID(deps_dict["project_id"])
    deps_dict["notebook"] = OrderedDict(deps_dict.get("notebook", {}))
    return AnalysisDeps(**deps_dict)


def _reconstruct_swe_deps(deps_dict: dict) -> SWEDeps:
    deps_dict["orchestrator_id"] = UUID(deps_dict["orchestrator_id"])
    deps_dict["project_path"] = Path(deps_dict["project_path"])
    deps_dict["project_id"] = UUID(deps_dict["project_id"])
    if "modified_files" not in deps_dict:
        deps_dict["modified_files"] = {}
    return SWEDeps(**deps_dict)


def _reconstruct_orchestrator_deps(deps_dict: dict) -> OrchestratorDeps:
    deps_dict["run_id"] = UUID(deps_dict["run_id"])
    deps_dict["project_id"] = UUID(deps_dict["project_id"])
    deps_dict["project_path"] = Path(deps_dict["project_path"])
    return OrchestratorDeps(**deps_dict)


async def main(project_name: str) -> str:

    logger.info("Setting up project...")

    project_id = uuid4()
    run_id = uuid4()
    try:
        package_name = "experiments"
        image_name = "research-sandbox"
        container_name = str(project_id)
        project_path = await create_project_container_if_not_exists(project_id, package_name, image_name)
        await install_package_after_start(container_name, package_name)

        project_dir = PROJECTS_DIR / project_name
        with open(project_dir / "description.txt", "r") as f:
            deliverable_description = f.read()
            data_dir = project_dir / "data"

            logger.info(f"Copying data directory to container: {data_dir}")
            container_data_path = await copy_file_or_directory_to_container(
                data_dir,
                project_path / "data",
                container_name,
                zip=True
            )

            data_structure = await get_folder_structure_description(
                container_name,
                path=container_data_path,
                n_levels=10,
                max_lines=200
            )

        orchestrator_deps = OrchestratorDeps(
            run_id=run_id,
            container_name=container_name,
            project_id=project_id,
            package_name=package_name,
            project_path=project_path
        )

        deliverable_description = (
            f"{deliverable_description}\n\n"
            f"The data directory structure:\n{data_structure}\n\n"
            f"The data is available at: {container_data_path}"
        )
        logger.info(f"Deliverable description: {deliverable_description}")
        await run_orchestrator(deliverable_description, orchestrator_deps)

    except (KeyboardInterrupt, Exception) as e:
        logger.error(f"Error or interrupt occurred: {e}, cleaning up...")
        delete_project_container_if_exists(project_id)
        raise


if __name__ == "__main__":
    project_name = "tumor_segmentation"
    asyncio.run(main(project_name))
