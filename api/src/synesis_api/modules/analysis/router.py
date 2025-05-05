import uuid
from typing import Annotated, List
from pathlib import Path
from fastapi import APIRouter, Depends, HTTPException
from .schema import AnalysisJobResultMetadata, AnalysisJobResultMetadataList, AnalysisRequest, AnalysisJobResult
from ...auth.service import (create_api_key,
                             get_current_user,
                             user_owns_job)
from .service import (
    run_analysis_planner_job,
    get_analysis_job_results_from_db,
    get_user_analysis_metadata,
    create_pdf_from_results,
    get_dataset_ids_by_job_id,
)
from ..jobs.service import create_job, get_job_metadata, update_job_status
from ..jobs.schema import JobMetadata
from ...auth.schema import User
from ..ontology.service import get_user_datasets_by_ids
router = APIRouter()

@router.post("/run-analysis-planner", response_model=JobMetadata)
async def run_analysis_planner(
    analysis_request: AnalysisRequest,
    user: Annotated[User, Depends(get_current_user)] = None,
) -> JobMetadata:
    
    if analysis_request.job_id is None and analysis_request.prompt is None:
        raise HTTPException(
            status_code=400, detail="You need to provide a desired change.")

    if analysis_request.job_id is None:
        try:
            api_key = await create_api_key(user)
            analysis_job = await create_job(user.id, api_key.id, "analysis")
            prev_job_results = None
        except:
            raise HTTPException(
                status_code=500, detail="Failed to create analysis job.")
    else:
        analysis_job = await get_job_metadata(analysis_request.job_id)
        prev_job_results = await get_analysis_job_results(analysis_request.job_id, user)
        dataset_ids = await get_dataset_ids_by_job_id(analysis_request.job_id)
        # automation_ids = await get_automation_by_job_id(analysis_request.job_id)
        analysis_request.dataset_ids = dataset_ids
        # analysis_request.automation_ids = automation_ids
        await update_job_status(analysis_request.job_id, "running")
        
    if len(analysis_request.dataset_ids) == 0 and len(analysis_request.automation_ids) == 0:
        raise HTTPException(
            status_code=400, detail="At least one dataset or automation is required.")
    
    # if len(automations) == 0:
    #     problem_description = "No problem description provided."

    # Get datasets and automations from database
    try: 
        datasets = await get_user_datasets_by_ids(user.id, analysis_request.dataset_ids)
    except:
        raise HTTPException(
            status_code=500, detail="Failed to get datasets.")

    # TODO: Get automations from database

    data_dir = Path("integrated_data") / f"{user.id}"
    data_paths = [data_dir / f"{dataset_id}.csv" for dataset_id in analysis_request.dataset_ids]
    problem_description = "" # should come from Automation
    
    try:
        job_results = await run_analysis_planner_job.kiq(
            analysis_job.id,
            user.id,
            datasets.time_series,
            problem_description,
            analysis_request.prompt,
            prev_job_results
        )
    except:
        await update_job_status(analysis_job.id, "failed")
        raise HTTPException(
            status_code=500, detail="Failed to run analysis planner.")
    
    return analysis_job 
        

# @router.post("/call-analysis-agent", response_model=JobMetadata)
# async def call_analysis_agent(
#     dataset_ids: List[uuid.UUID],
#     automation_ids: List[uuid.UUID],
#     user: Annotated[User, Depends(get_current_user)] = None,

# ):
#     # datasets = await get_user_time_series_dataset_by_id(dataset_ids, user.id)
#     # automations = await get_user_automation_by_id(automation_ids, user.id) # TODO: add automation support

#     try:
#         api_key = await create_api_key(user)
#         analysis_job = await create_job(user.id, api_key.id, "analysis")
#     except:
#         raise HTTPException(
#             status_code=500, detail="Failed to create analysis job.")
    
#     data_dir = Path("integrated_data") / f"{user.id}"
#     data_path = data_dir / f"{dataset_id}.csv"
#     project_description = ""
#     try:
#         summary = run_eda_job.apply_async(
#             args=[eda_job.id, dataset.id, str(
#                 data_path), dataset.description, project_description] # do we need this?
#         )
#     except:
#         raise HTTPException(status_code=500, detail="Failed to run EDA job.")
#     return analysis_job


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
