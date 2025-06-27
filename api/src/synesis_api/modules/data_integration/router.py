import uuid
import json
import time
import redis
import pandas as pd
from typing import Annotated, List
from fastapi import APIRouter, Depends, HTTPException, UploadFile, Form
from fastapi.responses import StreamingResponse
from io import StringIO
from synesis_api.modules.data_integration.service import (
    validate_restructured_data,
    get_job_results_from_job_id,
    get_integration_messages
)
from synesis_api.modules.ontology.service import create_dataset
from synesis_api.modules.data_integration.schema import (
    DataSubmissionResponse,
    IntegrationJobResult,
    IntegrationAgentState,
    IntegrationAgentFeedback,
    IntegrationMessage
)
from synesis_api.modules.automation.service import get_all_models_public_or_owned, get_model_joined, get_user_models, user_owns_model
from synesis_api.modules.automation.schema import ModelJoined
from synesis_api.modules.jobs.schema import JobMetadata
from synesis_api.auth.schema import User
from synesis_api.auth.service import (get_current_user,
                                      get_user_from_api_key,
                                      delete_api_key,
                                      user_owns_job)
from synesis_api.modules.jobs.service import get_job_metadata, update_job_status
from synesis_api.redis import get_redis
from synesis_api.agents.data_integration.local_agent.runner import LocalDataIntegrationRunner

router = APIRouter()

SSE_MAX_TIMEOUT = 3600

# TODO:
# - DB should only commit on end to avoid partial updates
# - Figure out whether to raise http exception in service or just router
# - Possibly simplify structure of router / service / agent


@router.post("/call-integration-agent", response_model=JobMetadata)
async def call_integration_agent(
    files: list[UploadFile],
    data_description: str = Form(...),
    data_source: str = Form(...),
    user: Annotated[User | None, Depends(get_current_user)] = None
) -> JobMetadata:

    if data_source == "local":
        runner = LocalDataIntegrationRunner(user)
        integration_job = await runner(files, data_description)
    else:
        raise HTTPException(
            status_code=400, detail="Invalid data source, currently only local data source is supported")

    return integration_job


@router.post("/integration-agent-feedback", response_model=JobMetadata)
async def integration_agent_feedback(
        feedback: IntegrationAgentFeedback,
        redis_stream: Annotated[redis.Redis, Depends(get_redis)],
        user: Annotated[User, Depends(get_current_user)] = None) -> JobMetadata:

    if not await user_owns_job(user.id, feedback.job_id):
        raise HTTPException(
            status_code=403, detail="You do not have permission to access this job")

    integration_job = await get_job_metadata(feedback.job_id)

    if integration_job.status == "completed":
        raise HTTPException(
            status_code=400, detail="Integration job is already completed")

    try:
        runner = LocalDataIntegrationRunner(user, feedback.job_id)
        integration_job = await runner.resume_job_from_feedback(feedback.content, redis_stream)
        return integration_job

    except Exception as e:
        raise HTTPException(
            status_code=500, detail=f"Failed to process the integration request: {str(e)}")


@router.post("/integration-agent-approve/{job_id}", response_model=JobMetadata)
async def integration_agent_approve(
        job_id: uuid.UUID,
        user: Annotated[User, Depends(get_current_user)] = None) -> JobMetadata:

    if not await user_owns_job(user.id, job_id):
        raise HTTPException(
            status_code=403, detail="You do not have permission to access this job")

    integration_job = await get_job_metadata(job_id)

    if integration_job.status == "completed":
        raise HTTPException(
            status_code=400, detail="Integration job is already completed")

    await update_job_status(job_id, "completed")
    integration_job.status = "completed"
    return integration_job


@router.get("/integration-messages/{job_id}")
async def integration_messages(
    job_id: uuid.UUID,
    user: Annotated[User, Depends(get_current_user)] = None,
    include_cached: bool = True
) -> list[IntegrationMessage]:

    if not user or not await user_owns_job(user.id, job_id):
        raise HTTPException(
            status_code=403, detail="You do not have permission to access this job")

    # Fetch messages from DB
    return await get_integration_messages(job_id, include_cached=include_cached)


@router.get("/integration-agent-sse/{job_id}")
async def integration_agent_sse(
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

                # Don't send pydantic_ai_state to human, but send all other messages
                if data["type"] != "pydantic_ai_state":
                    yield f"data: {json.dumps(data)}\n\n"

            if start_time + timeout < time.time():
                break

    return StreamingResponse(stream_job_updates(), media_type="text/event-stream")


@router.get("/integration-agent-history/{job_id}")
async def get_integration_agent_history(
    job_id: uuid.UUID,
    cache: Annotated[redis.Redis, Depends(get_redis)],
    user: Annotated[User, Depends(get_current_user)] = None
) -> list[IntegrationAgentState]:

    if not user or not await user_owns_job(user.id, job_id):
        raise HTTPException(
            status_code=403, detail="You do not have permission to access this job")

    stream_key = str(job_id)
    data = await cache.xread({stream_key: 0}, count=None)

    states = [item[1]["content"]
              for item in data[0][1] if item[1]["type"] == "agent_state"]
    states = [IntegrationAgentState(agent_state=state) for state in states]

    return states


# TODO: Make efficient
@router.post("/restructured-data", response_model=DataSubmissionResponse)
async def post_restructured_data(
    data: UploadFile,
    metadata: UploadFile,
    mapping: UploadFile,
    data_description: str = Form(...),
    dataset_name: str = Form(...),
    data_modality: str = Form(...),
    index_first_level: str = Form(...),
    index_second_level: str | None = Form(None),
    job_id: str = Form(...),
    user: Annotated[User, Depends(get_user_from_api_key)] = None,
) -> DataSubmissionResponse:

    try:
        job_id = uuid.UUID(job_id)
    except ValueError:
        raise HTTPException(
            status_code=400, detail="Invalid job_id format. Must be a valid UUID.")

    if data.content_type != "text/csv":
        raise HTTPException(
            status_code=400, detail="The data file must be a CSV file")

    data_content = await data.read()
    metadata_content = await metadata.read()
    mapping_content = await mapping.read()

    data_df = pd.read_csv(StringIO(data_content.decode("utf-8")))
    metadata_df = pd.read_csv(StringIO(metadata_content.decode("utf-8")))
    mapping_dict = json.loads(mapping_content.decode("utf-8"))

    data_df, metadata_df, mapping_dict = validate_restructured_data(
        data_df,
        metadata_df,
        mapping_dict,
        index_first_level,
        index_second_level
    )

    dataset_id = await create_dataset(
        data_df,
        metadata_df,
        data_description,
        dataset_name,
        data_modality,
        user.id,
        job_id
    )

    await delete_api_key(user)

    return DataSubmissionResponse(dataset_id=dataset_id)


@router.get("/integration-job-results/{job_id}", response_model=IntegrationJobResult)
async def get_integration_job_results(
    job_id: uuid.UUID,
    user: Annotated[User, Depends(get_current_user)] = None
) -> IntegrationJobResult:

    if not user or not await user_owns_job(user.id, job_id):
        raise HTTPException(
            status_code=403, detail="You do not have permission to access this job")

    job_metadata = await get_job_metadata(job_id)

    if job_metadata.status == "completed":
        return await get_job_results_from_job_id(job_id)
    else:
        raise HTTPException(
            status_code=202, detail="Integration job is still running")
