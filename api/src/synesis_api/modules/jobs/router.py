import uuid
from fastapi import APIRouter, Depends, HTTPException
from typing import List
from ...auth.schema import User
from ...auth.service import get_current_user
from .schema import JobMetadata
from .service import get_job_metadata, get_jobs


router = APIRouter()


@router.get("/jobs/{job_id}", response_model=JobMetadata)
async def get_job(
    job_id: uuid.UUID,
    current_user: User = Depends(get_current_user)
) -> JobMetadata:
    job = await get_job_metadata(job_id)
    if job.user_id != current_user.id:
        raise HTTPException(
            status_code=403, detail="Not authorized to access this job")
    return job


@router.get("/jobs", response_model=List[JobMetadata])
async def list_jobs(
    only_running: bool = False,
    current_user: User = Depends(get_current_user)
) -> List[JobMetadata]:
    return await get_jobs(current_user.id, only_running=only_running)


@router.post("/jobs/batch", response_model=List[JobMetadata])
async def batch_jobs(
    job_ids: List[uuid.UUID],
    current_user: User = Depends(get_current_user)
) -> List[JobMetadata]:
    return await get_jobs(current_user.id, job_ids)
