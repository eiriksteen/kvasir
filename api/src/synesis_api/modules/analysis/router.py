import uuid
from typing import Annotated
from pathlib import Path
from fastapi import APIRouter, Depends, HTTPException
from synesis_api.modules.analysis.schema import EDAJobResult
from synesis_api.auth.service import (create_api_key,
                                      get_current_user,
                                      user_owns_job)
from synesis_api.modules.analysis.service import (
    run_eda_job,
    get_job_results
)
from synesis_api.modules.jobs.service import create_job, get_job_metadata
from synesis_api.modules.jobs.schema import JobMetadata
from synesis_api.auth.schema import User
from synesis_api.modules.ontology.service import get_user_time_series_dataset_by_id


router = APIRouter()


@router.post("/call-eda-agent", response_model=JobMetadata)
async def call_eda_agent(
    data_id: uuid.UUID,
    user: Annotated[User, Depends(get_current_user)] = None,

):
    print(data_id)
    print(user.id)
    dataset = await get_user_time_series_dataset_by_id(data_id, user.id)

    print(1)
    try:
        eda_job = await create_job(user.id, "eda")
    except:
        raise HTTPException(
            status_code=500, detail="Failed to create EDA job.")
    print(2)
    data_dir = Path("integrated_data") / f"{user.id}"
    data_path = data_dir / f"{data_id}.csv"
    project_description = ""
    print(3)
    try:
        summary = run_eda_job.apply_async(
            args=[eda_job.id, user.id, str(
                data_path), dataset.description, project_description] # do we need this?
        )
    except:
        raise HTTPException(status_code=500, detail="Failed to run EDA job.")
    print(4)
    return eda_job


@router.get("/eda-job-status/{eda_id}", response_model=JobMetadata)
async def get_eda_job_status(
    eda_id: uuid.UUID,
    user: Annotated[User, Depends(get_current_user)] = None
) -> JobMetadata:
    if not await user_owns_job(user.id, eda_id):
        raise HTTPException(
            status_code=403, detail="You do not have permission to access this job"
        )

    job_meta_data = await get_job_metadata(eda_id)
    return job_meta_data


@router.get("/eda-job-results/{eda_id}", response_model=EDAJobResult)
async def get_eda_job_results(
    eda_id: uuid.UUID,
    user: Annotated[User, Depends(get_current_user)] = None
) -> EDAJobResult:

    if not await user_owns_job(user.id, eda_id):
        raise HTTPException(
            status_code=403, detail="You do not have permission to access this job")

    job_metadata = await get_job_metadata(eda_id)
    if job_metadata.status == "completed":
        return await get_job_results(eda_id)

    else:
        raise HTTPException(
            status_code=500, detail="EDA job is still running")
