import uuid
from datetime import datetime
from celery import shared_task
from celery.utils.log import get_task_logger
from pathlib import Path
from sqlalchemy import select, insert, update
from asgiref.sync import async_to_sync
from ..database.service import execute, fetch_one
from .schema import ModelJobMetadataInDB, ModelJobResultInDB
from .models import model_jobs
from .agent.deps import ModelDeps
from .agent.agent import model_agent

from fastapi import HTTPException


logger = get_task_logger(__name__)


async def run_model_agent(
        project_id: uuid.UUID,
        data_path: str,
        problem_description: str,
        data_analysis: str
) -> ModelJobResultInDB:
    
    try:
        model_deps = ModelDeps(
            data_path=Path(data_path),
            data_analysis=data_analysis,
            problem_description=problem_description
        )
        
        output = await model_agent.run(
            "Create python code for the model and run it in the container.",
            deps=model_deps
        )
        print(output)
    except:
        raise HTTPException(status_code=500, detail="Failed during modeling.")
    
    logger.info("Running model completed")

    await execute(
        update(model_jobs).where(model_jobs.c.id == project_id).values(
            status="completed", completed_at=datetime.now()),
            commit_after=True
    )
    logger.info("Running model")

    output_in_db = ModelJobResultInDB(
        job_id = project_id,
        **output.data.model_dump()
    )
    
    return output_in_db

@shared_task
def run_model_job(args):
    async_to_sync(run_model_agent)(args)


async def get_job_metadata(model_id: uuid.UUID) -> ModelJobMetadataInDB:
    job = await fetch_one(
        select(model_jobs).where(model_jobs.c.id == model_id),
        commit_after=True
    )

    if job is None:
        raise HTTPException(
            status_code=404, detail="Job not found"
        )

    return ModelJobMetadataInDB(**job)


async def get_job_results(job_id: uuid.UUID) -> ModelJobResultInDB:

    metadata = await get_job_metadata(job_id)

    if metadata.status != "completed":
        raise HTTPException(status_code=400, detail="Job is not completed")

    results = await fetch_one(
        select(model_jobs_results).where(
            model_jobs_results.c.job_id == job_id),
        commit_after=True
    )

    return ModelJobResultInDB(**results)


async def create_model_job(user_id: uuid.UUID, api_key_id: uuid.UUID = None, job_id: uuid.UUID = None) -> ModelJobMetadataInDB:
    model_job = ModelJobMetadataInDB(
        id = job_id if job_id else uuid.uuid4(),
        status="running",
        api_key_id=api_key_id if api_key_id else uuid.uuid4(),
        user_id=user_id,
        started_at=datetime.now()
    )
    await execute(
        insert(model_jobs).values(model_job.model_dump()),
        commit_after=True
    )
    return model_job