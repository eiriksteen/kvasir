import asyncio
from pathlib import Path
from uuid import uuid4
from typing import List
from collections import OrderedDict

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
            break

        for analysis_run_to_launch in output.analysis_runs_to_launch:
            await run_analysis.kiq(analysis_run_to_launch.deliverable_description, AnalysisDeps(
                run_id=f"{analysis_run_to_launch.run_id}-{uuid4()}",
                container_name=deps.container_name,
                orchestrator_id=deps.run_id,
                data_paths=analysis_run_to_launch.data_paths,
                injected_analyses=analysis_run_to_launch.analyses_to_inject,
                project_path=deps.project_path,
                project_id=deps.project_id,
                notebook=OrderedDict()
            ))

        for analysis_run_to_resume in output.analysis_runs_to_resume:
            saved_deps = await get_saved_deps(analysis_run_to_resume.run_id)
            await run_analysis.kiq(analysis_run_to_resume.message, saved_deps)

        for swe_run_to_launch in output.swe_runs_to_launch:
            await run_swe.kiq(swe_run_to_launch.deliverable_description, SWEDeps(
                run_id=f"{swe_run_to_launch.run_id}-{uuid4()}",
                container_name=deps.container_name,
                orchestrator_id=deps.run_id,
                data_paths=swe_run_to_launch.data_paths,
                injected_analyses=swe_run_to_launch.analyses_to_inject,
                read_only_paths=swe_run_to_launch.read_only_paths,
                project_path=deps.project_path,
                project_id=deps.project_id
            ))

        for swe_run_to_resume in output.swe_runs_to_resume:
            saved_deps = await get_saved_deps(swe_run_to_resume.run_id)
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
        deps: AnalysisDeps) -> str:

    try:
        await save_deps(deps.run_id, deps)
        analysis_run = await analysis_agent.run(
            deliverable_description,
            deps=deps,
            message_history=await get_message_history(deps.run_id)
        )

        await save_message_history(deps.run_id, analysis_run.all_messages())
        await write_file_to_container(
            deps.project_path / "analysis" / f"{deps.run_id}.txt",
            analysis_run.output,
            deps.container_name
        )

        orchestrator_id_str = str(deps.orchestrator_id)
        await add_result_to_queue(orchestrator_id_str, analysis_run.output)

        if await get_run_status(orchestrator_id_str) == "waiting":
            orchestrator_deps = await get_saved_deps(orchestrator_id_str)
            await run_orchestrator("Continue processing results from the queue.", orchestrator_deps)

    except Exception as e:
        delete_project_container_if_exists(deps.project_id)
        raise e

    return analysis_run.output


@broker.task
async def run_swe(
        deliverable_description: str,
        deps: SWEDeps) -> str:

    try:
        await save_deps(deps.run_id, deps)

        swe_run = await swe_agent.run(
            deliverable_description,
            deps=deps,
            message_history=await get_message_history(deps.run_id)
        )

        await save_message_history(deps.run_id, swe_run.all_messages())
        await add_result_to_queue(deps.orchestrator_id, swe_run.output)

        if await get_run_status(deps.orchestrator_id) == "waiting":
            orchestrator_deps = await get_saved_deps(deps.orchestrator_id)
            await run_orchestrator("Continue processing results from the queue.", orchestrator_deps)

    except Exception as e:
        delete_project_container_if_exists(deps.project_id)
        raise e

    return swe_run.output


async def main(project_name: str) -> str:

    logger.info("Setting up project...")

    try:
        project_id = uuid4()
        package_name = "experiments"
        image_name = "research-sandbox"
        container_name = str(project_id)
        project_path = await create_project_container_if_not_exists(project_id, package_name, image_name)
        await install_package_after_start(container_name, package_name)

        # copy file_paths to container
        project_dir = PROJECTS_DIR / project_name
        with open(project_dir / "description.txt", "r") as f:
            deliverable_description = f.read()
            data_dir = project_dir / "data"
            file_paths = list(data_dir.glob("*"))
            container_file_paths = []
            logger.info(f"Copying files to container: {file_paths}")
            for file_path in file_paths:
                container_file_path = await copy_file_or_directory_to_container(file_path, project_path / "data" / file_path.name, container_name)
                container_file_paths.append(container_file_path)

        run_id = uuid4()
        orchestrator_deps = OrchestratorDeps(
            run_id=run_id,
            container_name=container_name,
            project_id=project_id,
            package_name=package_name,
            project_path=project_path
        )

        deliverable_description = f"{deliverable_description}\n\nThe relevant file paths are: {container_file_paths}"
        logger.info(f"Deliverable description: {deliverable_description}")
        await run_orchestrator(deliverable_description, orchestrator_deps)

    except Exception as e:
        delete_project_container_if_exists(project_id)
        raise e


if __name__ == "__main__":
    project_name = "ett_forecasting"
    asyncio.run(main(project_name))
