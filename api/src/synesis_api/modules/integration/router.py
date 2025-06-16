import uuid
import json
import time
import redis
import aiofiles
import redis
import pandas as pd
from datetime import datetime, timezone
from typing import Annotated
from fastapi import APIRouter, Depends, HTTPException, UploadFile, Form, WebSocket, WebSocketException
from fastapi.responses import StreamingResponse
from pydantic_ai.messages import UserPromptPart, ModelRequest
from pydantic_core import to_jsonable_python
from io import StringIO
from pathlib import Path
from synesis_api.modules.integration.service import (
    validate_restructured_data,
    get_job_results,
    get_integration_input,
    create_messages_pydantic,
    get_integration_messages,
    create_integration_input,
    delete_integration_result,
    get_dataset_id_from_job_id
)
from synesis_api.modules.integration.tasks import run_integration_job_task
from synesis_api.modules.ontology.service import create_dataset, delete_dataset
from synesis_api.modules.integration.schema import (
    DataSubmissionResponse,
    IntegrationJobResult,
    IntegrationAgentState,
    IntegrationAgentFeedback,
    IntegrationJobDirectoryInput,
    IntegrationMessage
)
from synesis_api.modules.chat.agent import chatbot_agent
from synesis_api.modules.jobs.schema import JobMetadata
from synesis_api.auth.schema import User
from synesis_api.auth.service import (create_api_key,
                                      get_current_user,
                                      get_user_from_api_key,
                                      delete_api_key,
                                      user_owns_job,
                                      )
from synesis_api.modules.jobs.service import create_job, get_job_metadata, update_job_status
from synesis_api.redis import get_redis

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
    user: Annotated[User, Depends(get_current_user)] = None
) -> JobMetadata:

    job_id = uuid.uuid4()

    if not user:
        raise HTTPException(
            status_code=401, detail="You must be logged in to call the integration agent")

    if data_source == "directory":
        data_directory = Path.cwd() / "data" / f"{user.id}" / f"{job_id}"
        data_directory.mkdir(parents=True, exist_ok=True)
        api_key = None

        try:
            # Save all files to the directory
            for file in files:
                relative_path = Path(file.filename)
                target_path = data_directory / relative_path
                target_path.parent.mkdir(parents=True, exist_ok=True)
                async with aiofiles.open(target_path, mode="wb") as f:
                    await f.write(await file.read())

            api_key = await create_api_key(user)

            job_name = await chatbot_agent.run(
                f"Give me a human-readable suitable name (with no quotes) for a data integration job based on the following description: '{data_description}'. The name should be short and concise. Output just the name!"
            )

            integration_job = await create_job(
                user.id,
                "integration",
                job_id=job_id,
                job_name=job_name.output
            )

            await create_integration_input(IntegrationJobDirectoryInput(
                job_id=job_id,
                data_description=data_description,
                data_directory=str(data_directory)
            ), data_source)

            await run_integration_job_task.kiq(
                job_id,
                api_key.key,
                str(data_directory),
                data_description,
                data_source
            )

            return integration_job

        except Exception as e:
            if data_directory and data_directory.exists():
                for file in data_directory.iterdir():
                    file.unlink()
                data_directory.rmdir()
            if api_key:
                await delete_api_key(user)
            raise HTTPException(
                status_code=500, detail=f"Failed to process the integration request: {str(e)}")

    else:
        raise HTTPException(
            status_code=400, detail="Invalid data source, currently only directory is supported")


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

    api_key = None

    try:
        if integration_job.status == "awaiting_approval":
            dataset_id = await get_dataset_id_from_job_id(feedback.job_id)
            await delete_dataset(dataset_id, user.id)
            await delete_integration_result(feedback.job_id)

        resume_prompt = UserPromptPart(content=feedback.content)
        new_messages = [ModelRequest(parts=[resume_prompt])]
        messages_bytes = json.dumps(
            to_jsonable_python(new_messages)).encode("utf-8")

        await create_messages_pydantic(feedback.job_id, messages_bytes)

        integration_message = {
            "id": str(uuid.uuid4()),
            "type": "feedback",
            "role": "user",
            "content": feedback.content,
            "timestamp": datetime.now(timezone.utc).isoformat()
        }

        await redis_stream.xadd(str(feedback.job_id), integration_message)

        integration_input = await get_integration_input(feedback.job_id)
        api_key = await create_api_key(user)

        await update_job_status(feedback.job_id, "running")

        await run_integration_job_task.kiq(
            feedback.job_id,
            api_key.key,
            str(integration_input.data_directory),
            integration_input.data_description,
            "directory"
        )


        # print(task)
        # if task.status == "FAILURE":
        #     raise HTTPException(
        #         status_code=500, detail="Failed to process the integration request")

        integration_job.status = "running"

        return integration_job

    except Exception as e:
        if api_key:
            await delete_api_key(user)  # cannot delete api key here since it is referenced from job table
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

        # messages = await get_integration_messages(job_id, include_cached=True)

        # for message in messages:
        #     yield f"data: {message.model_dump_json()}\n\n"

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
        return await get_job_results(job_id)
    else:
        raise HTTPException(
            status_code=202, detail="Integration job is still running")
