import uuid
from typing import Annotated, List
from pathlib import Path
from fastapi import APIRouter, Depends, HTTPException
from .schema import AnalysisJobResultMetadata, AnalysisJobResultMetadataList, AnalysisRequest, AnalysisJobResult
from ...auth.service import (create_api_key,
                             get_current_user,
                             user_owns_job)
from .service import (
    get_analysis_job_results_from_db,
    get_user_analysis_metadata,
    create_pdf_from_results,
    get_dataset_ids_by_job_id,
    delete_analysis_job_results_from_db
)
from ..jobs.service import create_job, get_job_metadata, update_job_status
from ..jobs.schema import JobMetadata
from ...auth.schema import User
from ..ontology.service import get_user_datasets_by_ids
router = APIRouter()
        

@router.get("/analysis-job-status/{job_id}", response_model=JobMetadata)
async def get_analysis_job_status(
    job_id: uuid.UUID,
    user: Annotated[User, Depends(get_current_user)] = None
) -> JobMetadata:
    if not await user_owns_job(user.id, job_id):
        raise HTTPException(
            status_code=403, detail="You do not have permission to access this job"
        )

    job_meta_data = await get_job_metadata(job_id)
    return job_meta_data


@router.get("/analysis-job-results/{job_id}", response_model=AnalysisJobResultMetadata)
async def get_analysis_job_results(
    job_id: uuid.UUID,
    user: Annotated[User, Depends(get_current_user)] = None
) -> AnalysisJobResultMetadata:

    if not await user_owns_job(user.id, job_id):
        raise HTTPException(
            status_code=403, detail="You do not have permission to access this job")

    job_metadata = await get_job_metadata(job_id)
    if job_metadata.status == "completed":
        return await get_analysis_job_results_from_db(job_id)

    else:
        raise HTTPException(
            status_code=500, detail="Analysis job is still running")
    
@router.get("/analysis-job-results", response_model=AnalysisJobResultMetadataList)
async def get_analysis_job_results_list(
    user: Annotated[User, Depends(get_current_user)] = None
) -> AnalysisJobResultMetadataList:
    return await get_user_analysis_metadata(user.id)


@router.post("/create-analysis-pdf/{job_id}", response_model=AnalysisJobResultMetadata)
async def create_analysis_pdf(
    job_id: uuid.UUID,
    user: Annotated[User, Depends(get_current_user)] = None
) -> AnalysisJobResultMetadata:
    if not await user_owns_job(user.id, job_id):
        raise HTTPException(
            status_code=403, detail="You do not have permission to access this job")
    
    job_metadata = await get_job_metadata(job_id)
    
    if job_metadata.status == "completed":
        job_results = await get_analysis_job_results_from_db(job_id)
        await create_pdf_from_results(job_results, job_id)
    else:
        raise HTTPException(
            status_code=500, detail="Analysis job is still running")
    return job_results
    

@router.get("/analysis-result", response_model=AnalysisJobResultMetadataList)
async def get_analysis(
    user: Annotated[User, Depends(get_current_user)] = None
) -> AnalysisJobResultMetadataList:
    return await get_user_analysis_metadata(user.id)


@router.delete("/delete-analysis-job-results/{job_id}", response_model=uuid.UUID)
async def delete_analysis_job_results(
    job_id: uuid.UUID,
    user: Annotated[User, Depends(get_current_user)] = None
) -> uuid.UUID:
    if not await user_owns_job(user.id, job_id):
        raise HTTPException(
            status_code=403, detail="You do not have permission to access this job")
    return await delete_analysis_job_results_from_db(job_id)
