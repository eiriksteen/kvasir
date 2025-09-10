import uuid
import json
import time
from typing import Annotated, List
from fastapi import APIRouter, Depends, HTTPException
from fastapi.responses import StreamingResponse
from synesis_api.redis import get_redis
import redis
from synesis_api.auth.service import get_current_user, user_owns_runs
from synesis_schemas.main_server import User

router = APIRouter()

SSE_MAX_TIMEOUT = 300  # 5 minutes


@router.get("/analysis-agent-sse/{job_id}")
async def analysis_agent_sse(
    job_id: uuid.UUID,
    cache: Annotated[redis.Redis, Depends(get_redis)],
    timeout: int = SSE_MAX_TIMEOUT,
    user: Annotated[User, Depends(get_current_user)] = None
) -> StreamingResponse:

    if not user or not await user_owns_runs(user.id, [job_id]):
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

                # Don't send pydantic_ai_state to human, but send all other messages
                if data["type"] != "pydantic_ai_state":
                    yield f"data: {json.dumps(data)}\n\n"

            if start_time + timeout < time.time():
                break

    return StreamingResponse(stream_job_updates(), media_type="text/event-stream")


# @router.get("/analysis-job-status/{job_id}", response_model=RunInDB)
# async def get_analysis_job_status(
#     job_id: uuid.UUID,
#     user: Annotated[User, Depends(get_current_user)] = None
# ) -> Run:
#     if not await user_owns_run(user.id, job_id):
#         raise HTTPException(
#             status_code=403, detail="You do not have permission to access this job"
#         )

#     job_meta_data = await get_job(job_id)
#     return job_meta_data


@router.get("/analysis-job-results/{job_id}",)
async def get_analysis_job_results(
    job_id: uuid.UUID,
    user: Annotated[User, Depends(get_current_user)] = None
):

    # NOt implemented
    raise HTTPException(
        status_code=500, detail="Not implemented")


@router.get("/analysis-job-results", response_model=List)
async def get_analysis_job_results_list(
    user: Annotated[User, Depends(get_current_user)] = None
) -> List:
    return []


@router.post("/create-analysis-pdf/{run_id}", response_model=List)
async def create_analysis_pdf(
    run_id: uuid.UUID,
    user: Annotated[User, Depends(get_current_user)] = None
) -> List:
    return []


@router.get("/analysis-result", response_model=List)
async def get_analysis(
    user: Annotated[User, Depends(get_current_user)] = None
) -> List:
    return []


# @router.delete("/delete-analysis-job-results/{run_id}", response_model=uuid.UUID)
# async def delete_analysis_job_results(
#     run_id: uuid.UUID,
#     user: Annotated[User, Depends(get_current_user)] = None
# ) -> uuid.UUID:
#     if not await user_owns_run(user.id, run_id):
#         raise HTTPException(
#             status_code=403, detail="You do not have permission to access this job")
#     return await delete_analysis_job_results_from_db(run_id)
