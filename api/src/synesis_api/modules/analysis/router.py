import uuid
from typing import Annotated, List
from pathlib import Path
from fastapi import APIRouter, Depends, HTTPException
from synesis_api.modules.analysis.schema import EDAJobResult
from synesis_api.auth.service import (create_api_key,
                                      get_current_user,
                                      user_owns_job)

from synesis_api.modules.analysis.service import (
    # run_analysis_execution_job,
    run_analysis_planner_job,
    get_job_results,
    get_user_analysis_metadata,
    create_pdf_from_results,
    test_task
)
from synesis_api.modules.jobs.service import create_job, get_job_metadata
from synesis_api.modules.jobs.schema import JobMetadata
from synesis_api.auth.schema import User
from synesis_api.modules.ontology.service import get_user_time_series_dataset_by_id

router = APIRouter()

# TODO: Implement caching for datasets and automations

@router.post("/run-analysis-planner", response_model=AnalysisPlan)
async def run_analysis_planner(
    analysis_planner_request: AnalysisPlannerRequest,
    user: Annotated[User, Depends(get_current_user)] = None,
) -> AnalysisPlan:
    print(analysis_planner_request)
    if len(analysis_planner_request.time_series) == 0 and len(analysis_planner_request.tabular) == 0:
        raise HTTPException(
            status_code=400, detail="At least one dataset is required.")
    
    # if len(automations) == 0:
    #     problem_description = "No problem description provided."

    try:
        api_key = await create_api_key(user)
        analysis_job = await create_job(user.id, api_key.id, "analysis")
    except:
        raise HTTPException(
            status_code=500, detail="Failed to create analysis job.")
    

    data_dir = Path("integrated_data") / f"{user.id}"
    data_paths = [data_dir / f"{dataset.id}.csv" for dataset in analysis_planner_request.time_series]
    problem_description = "" # should come from Automation
    data_type = "time_series"

    return await run_analysis_planner_job.kiq(
        analysis_job.id,
        # data_paths,
        analysis_planner_request.time_series,
        # automations
        problem_description,
        analysis_planner_request.prompt,
    )

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
        return await get_job_results(job_id)

    else:
        raise HTTPException(
            status_code=500, detail="Analysis job is still running")


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
        job_results = await get_job_results(job_id)
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
