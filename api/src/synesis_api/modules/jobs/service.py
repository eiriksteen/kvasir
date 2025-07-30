import uuid
from datetime import datetime, timezone
from fastapi import HTTPException
from sqlalchemy import select, insert, update, delete
from synesis_api.modules.jobs.models import job
from synesis_api.modules.jobs.schema import JobInDB
from synesis_api.database.service import execute, fetch_one, fetch_all
from typing import List, Optional


async def create_job(
    user_id: uuid.UUID,
    job_type: str,
    conversation_id: Optional[uuid.UUID] = None,
    job_id: Optional[uuid.UUID] = None,
    job_name: Optional[str] = None,
) -> JobInDB:

    job_record = JobInDB(
        id=job_id if job_id else uuid.uuid4(),
        conversation_id=conversation_id,
        type=job_type,
        user_id=user_id,
        status="running",
        started_at=datetime.now(timezone.utc),
        job_name=job_name
    )

    await execute(
        insert(job).values(job_record.model_dump()),
        commit_after=True
    )

    return job_record


async def get_job(job_id: uuid.UUID) -> JobInDB:
    job_record = await fetch_one(
        select(job).where(job.c.id == job_id),
    )

    if job_record is None:
        raise HTTPException(
            status_code=404, detail="Job not found"
        )

    return JobInDB(**job_record)


async def get_jobs_by_conversation_id(conversation_id: uuid.UUID) -> List[JobInDB]:
    job_records = await fetch_all(
        select(job).where(job.c.conversation_id == conversation_id),
    )

    return [JobInDB(**job_record) for job_record in job_records]


async def get_jobs(
        user_id: uuid.UUID,
        job_ids: List[uuid.UUID] | None = None,
        only_running: bool = False,
        type: str | None = None) -> List[JobInDB]:

    query = select(job).where(job.c.user_id == user_id)
    if job_ids is not None:
        if len(job_ids) > 0:
            query = query.where(job.c.id.in_(job_ids))
        else:
            raise HTTPException(
                status_code=400, detail="Job IDs must be non-empty")
    if only_running:
        query = query.where(job.c.status == "running")
    if type is not None:
        query = query.where(job.c.type == type)
    query = query.order_by(job.c.started_at.desc())

    job_records = await fetch_all(query)

    return [JobInDB(**job_record) for job_record in job_records]


async def update_job_status(job_id: uuid.UUID, status: str) -> JobInDB:
    if status in ["completed", "failed"]:
        await execute(
            update(job).where(job.c.id == job_id).values(
                status=status,
                completed_at=datetime.now(timezone.utc)
            ),
            commit_after=True
        )
    else:
        await execute(
            update(job).where(job.c.id == job_id).values(
                status=status
            ),
            commit_after=True
        )

    return await get_job(job_id)


async def delete_job_by_id(job_id: uuid.UUID):
    await execute(
        delete(job).where(job.c.id == job_id),
        commit_after=True
    )
