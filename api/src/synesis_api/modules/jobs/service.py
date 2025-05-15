import uuid
from datetime import datetime, timezone
from fastapi import HTTPException
from sqlalchemy import select, insert, update
from synesis_api.modules.jobs.models import jobs
from synesis_api.modules.jobs.schema import JobMetadataInDB
from synesis_api.database.service import execute, fetch_one, fetch_all
from typing import List


async def create_job(
    user_id: uuid.UUID,
    job_type: str,
    job_id: uuid.UUID | None = None,
    job_name: str | None = None
) -> JobMetadataInDB:

    job = JobMetadataInDB(
        id=job_id if job_id else uuid.uuid4(),
        type=job_type,
        user_id=user_id,
        status="running",
        started_at=datetime.now(timezone.utc),
        job_name=job_name
    )

    await execute(
        insert(jobs).values(job.model_dump()),
        commit_after=True
    )

    return job


async def get_job_metadata(job_id: uuid.UUID) -> JobMetadataInDB:
    job = await fetch_one(
        select(jobs).where(jobs.c.id == job_id),
        commit_after=True
    )

    if job is None:
        raise HTTPException(
            status_code=404, detail="Job not found"
        )

    return JobMetadataInDB(**job)


async def get_jobs(
        user_id: uuid.UUID,
        job_ids: List[uuid.UUID] | None = None,
        only_running: bool = False,
        type: str | None = None) -> List[JobMetadataInDB]:

    query = select(jobs).where(jobs.c.user_id == user_id)
    if job_ids is not None:
        if len(job_ids) > 0:
            query = query.where(jobs.c.id.in_(job_ids))
        else:
            raise HTTPException(
                status_code=400, detail="Job IDs must be non-empty")
    if only_running:
        query = query.where(jobs.c.status == "running")
    if type is not None:
        query = query.where(jobs.c.type == type)
    query = query.order_by(jobs.c.started_at.desc())

    result = await fetch_all(query)

    return [JobMetadataInDB(**job) for job in result]


async def update_job_status(job_id: uuid.UUID, status: str):
    if status in ["completed", "failed"]:
        await execute(
            update(jobs).where(jobs.c.id == job_id).values(
                status=status,
                completed_at=datetime.now(timezone.utc)
            ),
            commit_after=True
        )
    else:
        await execute(
            update(jobs).where(jobs.c.id == job_id).values(
                status=status
            ),
            commit_after=True
        )
