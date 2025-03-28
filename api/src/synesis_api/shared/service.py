import uuid
from datetime import datetime
from fastapi import HTTPException
from sqlalchemy import select, insert, update
from .models import jobs
from .schema import IntegrationJobMetadataInDB
from ..database.service import execute, fetch_one, fetch_all
from typing import List


async def create_job(
    user_id: uuid.UUID,
    api_key_id: uuid.UUID,
    job_type: str,
    job_id: uuid.UUID | None = None
) -> IntegrationJobMetadataInDB:

    job = IntegrationJobMetadataInDB(
        id=job_id if job_id else uuid.uuid4(),
        type=job_type,
        user_id=user_id,
        api_key_id=api_key_id,
        status="running",
        started_at=datetime.now()
    )

    await execute(
        insert(jobs).values(job.model_dump()),
        commit_after=True
    )

    return job


async def get_job_metadata(job_id: uuid.UUID) -> IntegrationJobMetadataInDB:
    job = await fetch_one(
        select(jobs).where(jobs.c.id == job_id),
        commit_after=True
    )

    if job is None:
        raise HTTPException(
            status_code=404, detail="Job not found"
        )

    return IntegrationJobMetadataInDB(**job)


async def get_jobs(user_id: uuid.UUID, only_running: bool = False) -> List[IntegrationJobMetadataInDB]:
    query = select(jobs).where(jobs.c.user_id == user_id)
    if only_running:
        query = query.where(jobs.c.status == "running")
    query = query.order_by(jobs.c.started_at.desc())

    result = await fetch_all(
        query,
        commit_after=True
    )

    return [IntegrationJobMetadataInDB(**job) for job in result]


async def update_job_status(job_id: uuid.UUID, status: str):
    await execute(
        update(jobs).values(
            status=status,
            completed_at=datetime.now() if status in [
                "completed", "failed"] else None
        ).where(jobs.c.id == job_id),
        commit_after=True
    )
