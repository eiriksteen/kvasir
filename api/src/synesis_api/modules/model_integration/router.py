import uuid
import json
import time
import redis
from typing import Annotated
from fastapi import APIRouter, Depends, HTTPException, UploadFile, Form
from fastapi.responses import StreamingResponse
from synesis_api.modules.model_integration.service import (
    get_model_integration_job_results,
    get_model_integration_messages
)
from synesis_api.modules.model_integration.schema import (
    ModelIntegrationJobResult,
    ModelIntegrationMessage,
    ModelIntegrationJobInput
)
# from synesis_api.agents.model_integration.runner import run_model_integration_task
from synesis_api.agents.model_integration_alt.runner import run_model_integration_task
from synesis_api.modules.jobs.schema import JobMetadata
from synesis_api.auth.schema import User
from synesis_api.auth.service import get_current_user, user_owns_job
from synesis_api.modules.jobs.service import get_job_metadata, create_job
from synesis_api.redis import get_redis

router = APIRouter()

SSE_MAX_TIMEOUT = 3600


@router.post("/call-model-integration-agent", response_model=JobMetadata)
async def call_model_integration_agent(
    model_integration_job_input: ModelIntegrationJobInput,
    user: Annotated[User | None, Depends(get_current_user)] = None
) -> JobMetadata:

    try:
        job = await create_job(
            user_id=user.id,
            job_type="model_integration",
            job_name=f"Model integration {model_integration_job_input.model_id}"
        )

        await run_model_integration_task.kiq(
            user_id=user.id,
            model_id=model_integration_job_input.model_id,
            job_id=job.id,
            source=model_integration_job_input.source
        )

        return job

    except Exception as e:
        raise HTTPException(
            status_code=400, detail=f"Model integration job failed: {str(e)}")


@router.get("/model-integration-messages/{job_id}")
async def model_integration_messages(
    job_id: uuid.UUID,
    user: Annotated[User, Depends(get_current_user)] = None,
    include_cached: bool = True
) -> list[ModelIntegrationMessage]:

    if not user or not await user_owns_job(user.id, job_id):
        raise HTTPException(
            status_code=403, detail="You do not have permission to access this job")

    # Fetch messages from DB
    return await get_model_integration_messages(job_id, include_cached=include_cached)


@router.get("/model-integration-agent-sse/{job_id}")
async def model_integration_agent_sse(
    job_id: uuid.UUID,
    cache: Annotated[redis.Redis, Depends(get_redis)],
    timeout: int = SSE_MAX_TIMEOUT,
    user: Annotated[User, Depends(get_current_user)] = None
):

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

                # Don't send pydantic_ai_state to human, but send all other messages
                if data["type"] != "pydantic_ai_state":
                    yield f"data: {json.dumps(data)}\n\n"

            if start_time + timeout < time.time():
                break

    return StreamingResponse(stream_job_updates(), media_type="text/event-stream")


@router.get("/model-integration-job-results/{job_id}", response_model=ModelIntegrationJobResult)
async def get_model_integration_job_results(
    job_id: uuid.UUID,
    user: Annotated[User, Depends(get_current_user)] = None
) -> ModelIntegrationJobResult:

    if not user or not await user_owns_job(user.id, job_id):
        raise HTTPException(
            status_code=403, detail="You do not have permission to access this job")

    job_metadata = await get_job_metadata(job_id)

    if job_metadata.status != "completed":
        raise HTTPException(
            status_code=400, detail="Model integration job is not completed yet")

    try:
        results = await get_model_integration_job_results(job_id)
        return results
    except Exception as e:
        raise HTTPException(
            status_code=404, detail=f"Model integration results not found: {str(e)}")
