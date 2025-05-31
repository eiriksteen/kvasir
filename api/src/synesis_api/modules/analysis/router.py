import uuid
import json
import time
from typing import Annotated
from fastapi import APIRouter, Depends, HTTPException
from fastapi.responses import StreamingResponse
from synesis_api.redis import get_redis
import redis
from synesis_api.modules.analysis.schema import AnalysisJobResultMetadata, AnalysisJobResultMetadataList
from synesis_api.auth.service import get_current_user, user_owns_job
from synesis_api.modules.analysis.service import (
    get_analysis_job_results_from_db,
    get_user_analysis_metadata,
    create_pdf_from_results,
    delete_analysis_job_results_from_db
)
from synesis_api.modules.jobs.service import get_job_metadata
from synesis_api.modules.jobs.schema import JobMetadata
from synesis_api.auth.schema import User

router = APIRouter()

SSE_MAX_TIMEOUT = 300  # 5 minutes

@router.get("/analysis-agent-sse/{job_id}")
async def analysis_agent_sse(
    job_id: uuid.UUID,
    cache: Annotated[redis.Redis, Depends(get_redis)],
    timeout: int = SSE_MAX_TIMEOUT,
    user: Annotated[User, Depends(get_current_user)] = None
) -> StreamingResponse:

    if not user or not await user_owns_job(user.id, job_id):
            raise HTTPException(
                status_code=403, detail="You do not have permission to access this job")

    timeout = min(timeout, SSE_MAX_TIMEOUT)

    async def stream_job_updates():
        response = await cache.xread({str(job_id): "$"}, count=1, block=timeout*1000)
        start_time = time.time()
        last_id = response[0][1][-1][0] if response else None

        while True:
            response = await cache.xread({str(job_id): last_id}, count=1)

            if response:
                start_time = time.time()
                last_id = response[0][1][-1][0]
                data = response[0][1][0][1]
                print("data", data)

                # Don't send pydantic_ai_state to human, but send all other messages
                if data["type"] != "pydantic_ai_state":
                    yield f"data: {json.dumps(data)}\n\n"

            if start_time + timeout < time.time():
                break

    return StreamingResponse(stream_job_updates(), media_type="text/event-stream")

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
