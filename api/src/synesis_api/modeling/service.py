import uuid
import asyncio
from datetime import datetime
from celery import shared_task
from celery.utils.log import get_task_logger
from pathlib import Path
from sqlalchemy import update
from ..database.service import execute
from ..shared.service import get_job_metadata
from ..shared.models import jobs
from .schema import ModelJobResultInDB
from .agent.deps import ModelDeps
from .agent.agent import model_agent
from ..aws.service import upload_object_s3, retrieve_object

from fastapi import HTTPException


logger = get_task_logger(__name__)


async def run_model_agent(
        project_id: uuid.UUID,
        data_path: str,
        problem_description: str,
        data_analysis: str) -> ModelJobResultInDB:

    try:
        model_deps = ModelDeps(
            data_path=Path(data_path),
            data_analysis=data_analysis,
            problem_description=problem_description
        )
        nodes = []
        async with model_agent.iter(
            "Implement an AI model in python and run it in the container. Return the code and an explanation for how and which model you chose.",
            deps=model_deps
        ) as agent_run:

            async for node in agent_run:
                nodes.append(node)
                logger.info(f"Integration agent state: {node}")

            logger.info(
                f"Integration agent run completed for job {project_id}")

        output = agent_run.result.data
    except:
        raise HTTPException(status_code=500, detail="Failed during modeling.")

    await execute(
        update(jobs).where(jobs.c.id == project_id).values(
            status="completed", completed_at=datetime.now()),
        commit_after=True
    )
    logger.info("Model job updated in DB")

    output_in_db = ModelJobResultInDB(
        job_id=project_id,
        **output.model_dump()
    )

    logger.info("Model stored in S3")
    await upload_object_s3(output_in_db, "synesis-model", f"{project_id}.json")

    return output_in_db


@shared_task
def run_model_job(
    project_id: uuid.UUID,
    data_path: str,
    problem_description: str,
    data_analysis: str
):

    loop = asyncio.get_event_loop()
    loop.run_until_complete(run_model_agent(
        project_id, data_path, problem_description, data_analysis))


async def get_job_results(job_id: uuid.UUID) -> ModelJobResultInDB:

    metadata = await get_job_metadata(job_id)

    if metadata.status != "completed":
        raise HTTPException(status_code=400, detail="Job is not completed")

    json_data = await retrieve_object("synesis-model", f"{job_id}.json")

    return ModelJobResultInDB.model_validate_json(json_data)
