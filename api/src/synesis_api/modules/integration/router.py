import uuid
import json
import asyncio
import aiofiles
import redis
import pandas as pd
from typing import Annotated
from fastapi import APIRouter, Depends, HTTPException, UploadFile, Form, WebSocket
from io import StringIO
from pathlib import Path
from fastapi.responses import StreamingResponse
from .service import (
    run_integration_job,
    validate_restructured_data,
    insert_restructured_data_to_db,
    get_job_results
)
from .schema import DataSubmissionResponse, IntegrationJobResult, IntegrationAgentState
from ..jobs.schema import JobMetadata
from ...auth.schema import User
from ...auth.service import (create_api_key,
                             get_current_user,
                             get_user_from_api_key,
                             delete_api_key,
                             user_owns_job)
from ..jobs.service import create_job, get_job_metadata
from ...redis import get_redis


router = APIRouter()


@router.post("/call-integration-agent", response_model=JobMetadata)
async def call_integration_agent(
    files: list[UploadFile],
    data_description: str = Form(...),
    data_source: str = Form(...),
    user: Annotated[User, Depends(get_current_user)] = None
) -> JobMetadata:

    job_id = uuid.uuid4()

    if data_source == "directory":
        data_path = Path.cwd() / "data" / f"{user.id}" / f"{job_id}"
        data_path.mkdir(parents=True, exist_ok=True)
        api_key = None

        try:
            # Save all files to the directory
            for file in files:
                relative_path = Path(file.filename)
                target_path = data_path / relative_path
                target_path.parent.mkdir(parents=True, exist_ok=True)
                async with aiofiles.open(target_path, mode="wb") as f:
                    await f.write(await file.read())

            api_key = await create_api_key(user)

            integration_job = await create_job(
                user.id,
                api_key.id,
                "integration"
            )

            task = run_integration_job.apply_async(
                args=[integration_job.id,
                      api_key.key,
                      str(data_path),
                      data_description,
                      data_source]
            )

            if task.status == "FAILURE":
                raise HTTPException(
                    status_code=500, detail="Failed to process the integration request")

            return integration_job

        except Exception as e:
            if data_path and data_path.exists():
                data_path.unlink()
            if api_key:
                await delete_api_key(user)
            raise HTTPException(
                status_code=500, detail=f"Failed to process the integration request: {str(e)}")

    else:
        raise HTTPException(
            status_code=400, detail="Invalid data source, currently only directory is supported")


@router.websocket("/integration-agent-human-in-the-loop/{job_id}")
async def integration_agent_human_in_the_loop(
    job_id: uuid.UUID,
    websocket: WebSocket,
    cache: Annotated[redis.Redis, Depends(get_redis)],
    user: Annotated[User, Depends(get_current_user)] = None
):

    if not await user_owns_job(user.id, job_id):
        raise HTTPException(
            status_code=403, detail="You do not have permission to access this job")

    if not cache.exists(str(job_id)):
        raise HTTPException(status_code=404, detail="Job not found")

    await websocket.accept()

    while True:
        data = await cache.xread({str(job_id): 0}, count=1)[0][1][0][1]
        if "agent_message" in data:
            await websocket.send_json({"agent_message": data["agent_message"]})
        elif "ping_human" in data:
            await websocket.send_json({"ping_human": True})
            response = await websocket.receive_json()
            if "ping_human_response" in response:
                await cache.xadd(str(job_id), {"ping_human_response": response["ping_human_response"]})
        elif "help_message" in data:
            await websocket.send_json({"help_message": data["help_message"]})
            response = await websocket.receive_json()
            if "help_response" in response:
                await cache.xadd(str(job_id), {"help_response": response["help_response"]})

        await asyncio.sleep(0.1)


@router.get("/integration-agent-history/{job_id}")
async def get_integration_agent_history(
    job_id: uuid.UUID,
    cache: Annotated[redis.Redis, Depends(get_redis)],
    user: Annotated[User, Depends(get_current_user)] = None
) -> list[IntegrationAgentState]:

    if not await user_owns_job(user.id, job_id):
        raise HTTPException(
            status_code=403, detail="You do not have permission to access this job")

    stream_key = str(job_id)
    data = await cache.xread({stream_key: 0}, count=None)
    states = [item[1]["agent_state"] for item in data[0][1]]
    states = [IntegrationAgentState(agent_state=state) for state in states]

    return states


@router.get("/integration-agent-state/{job_id}")
async def get_integration_agent_state(
    job_id: uuid.UUID,
    cache: Annotated[redis.Redis, Depends(get_redis)],
    user: Annotated[User, Depends(get_current_user)] = None
) -> StreamingResponse:

    if not await user_owns_job(user.id, job_id):
        raise HTTPException(
            status_code=403, detail="You do not have permission to access this job")

    async def generate_agent_state():
        stream_key = str(job_id)
        last_id = 0
        while True:
            data = await cache.xread({stream_key: last_id}, count=1)
            if data:
                state = IntegrationAgentState(
                    agent_state=data[0][1][0][1]["agent_state"])
                yield state.model_dump_json()
                last_id = data[0][1][0][0]

    return StreamingResponse(generate_agent_state(), media_type="text/event-stream")


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
    user: Annotated[User, Depends(get_user_from_api_key)] = None
) -> DataSubmissionResponse:

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

    dataset_id = uuid.uuid4()
    save_path = Path.cwd() / "integrated_data" / f"{user.id}" / f"{dataset_id}"
    save_path.mkdir(parents=True, exist_ok=True)

    try:
        async with aiofiles.open(save_path / "data.csv", 'wb') as out_file:
            await out_file.write(data_df.reset_index().to_csv(index=False).encode("utf-8"))
    except OSError as e:
        raise HTTPException(
            status_code=500, detail=f"Failed to write output file: {str(e)}")

    dataset_id = await insert_restructured_data_to_db(
        data_df,
        data_description,
        dataset_name,
        data_modality,
        user.id,
        dataset_id
    )

    return DataSubmissionResponse(dataset_id=dataset_id)


@router.get("/integration-job-results/{job_id}", response_model=IntegrationJobResult)
async def get_integration_job_results(
    job_id: uuid.UUID,
    user: Annotated[User, Depends(get_current_user)] = None
) -> IntegrationJobResult:

    if not await user_owns_job(user.id, job_id):
        raise HTTPException(
            status_code=403, detail="You do not have permission to access this job")

    job_metadata = await get_job_metadata(job_id)

    if job_metadata.status == "completed":
        return await get_job_results(job_id)
    else:
        raise HTTPException(
            status_code=202, detail="Integration job is still running")
