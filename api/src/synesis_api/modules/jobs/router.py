import uuid
import asyncio
import json
from fastapi import APIRouter, Depends, HTTPException
from pydantic import TypeAdapter
from typing import List
from fastapi.responses import StreamingResponse
from synesis_api.auth.schema import User
from synesis_api.auth.service import get_current_user
from synesis_api.modules.jobs.schema import Job
from synesis_api.modules.jobs.service import get_job, get_jobs


router = APIRouter()


MIN_SLEEP_TIME = 5


@router.get("/jobs/{job_id}", response_model=Job)
async def fetch_job(
    job_id: uuid.UUID,
    current_user: User = Depends(get_current_user)
) -> Job:
    job = await get_job(job_id)

    if job.user_id != current_user.id:
        raise HTTPException(status_code=403, detail="Not authorized")

    return job


@router.get("/jobs", response_model=List[Job])
async def list_jobs(
    only_running: bool = False,
    type: str | None = None,
    current_user: User = Depends(get_current_user)
) -> List[Job]:

    return await get_jobs(current_user.id, only_running=only_running, type=type)


@router.get("/jobs-sse")
async def jobs_sse(
    job_type: str,
    current_user: User = Depends(get_current_user),
    sleep_time: int = MIN_SLEEP_TIME
) -> StreamingResponse:

    sleep_time = max(sleep_time, MIN_SLEEP_TIME)
    adapter = TypeAdapter(List[Job])
    all_jobs = await get_jobs(current_user.id, type=job_type)

    running_or_pending_job_ids = [
        job.id for job in all_jobs if job.status == "running" or job.status == "pending"]

    async def stream_jobs():

        while True:
            if not running_or_pending_job_ids:
                break
            jobs = await get_jobs(current_user.id, running_or_pending_job_ids)
            yield f"data: {adapter.dump_json(jobs, by_alias=True).decode("utf-8")}\n\n"
            await asyncio.sleep(sleep_time)

            if not any(job.status == "running" or job.status == "pending" for job in jobs):
                break

    return StreamingResponse(stream_jobs(), media_type="text/event-stream")


@router.post("/jobs/batch", response_model=List[Job])
async def batch_jobs(
    job_ids: List[uuid.UUID],
    current_user: User = Depends(get_current_user)
) -> List[Job]:

    return await get_jobs(current_user.id, job_ids)
