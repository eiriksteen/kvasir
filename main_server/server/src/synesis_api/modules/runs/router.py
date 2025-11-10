import uuid
import time
import redis
import asyncio
from datetime import datetime, timezone
from fastapi import APIRouter, Depends, HTTPException
from fastapi.responses import StreamingResponse, Response
from typing import Annotated, List, Optional
from pydantic import TypeAdapter

from synesis_api.auth.service import get_current_user, user_owns_runs, oauth2_scheme
from synesis_schemas.main_server import User
from synesis_api.redis import get_redis
from synesis_api.app_secrets import SSE_MAX_TIMEOUT, SSE_MIN_SLEEP_TIME
from synesis_schemas.main_server import (
    RunMessageInDB,
    Run,
    RunCreate,
    RunMessageCreate,
    RunStatusUpdate,
    RunMessageCreatePydantic,
    RunPydanticMessageInDB,
    RunInDB
)
from synesis_api.modules.runs.service import (
    get_runs,
    get_run_messages,
    create_run,
    create_run_message,
    update_run_status,
    create_run_message_pydantic,
    get_run_messages_pydantic,
    launch_run,
    reject_run
)
from synesis_api.client import MainServerClient


router = APIRouter()


@router.get("/runs")
async def fetch_runs(
    project_id: Optional[uuid.UUID] = None,
    user: Annotated[User, Depends(get_current_user)] = None
) -> List[Run]:
    runs = await get_runs(user.id, project_id=project_id)
    return runs


@router.post("/run")
async def post_run(
    request: RunCreate,
    user: Annotated[User, Depends(get_current_user)] = None
) -> RunInDB:

    run = await create_run(user.id, request)
    return run


@router.post("/launch-run/{run_id}")
async def post_launch_run(
        run_id: uuid.UUID,
        user: Annotated[User, Depends(get_current_user)] = None,
        token: str = Depends(oauth2_scheme)) -> RunInDB:

    if not await user_owns_runs(user.id, [run_id]):
        raise HTTPException(
            status_code=403, detail="You do not have permission to access this run")

    return await launch_run(user.id, MainServerClient(token), run_id)


@router.patch("/reject-run/{run_id}")
async def patch_reject_run(
        run_id: uuid.UUID,
        user: Annotated[User, Depends(get_current_user)] = None) -> RunInDB:

    if not await user_owns_runs(user.id, [run_id]):
        raise HTTPException(
            status_code=403, detail="You do not have permission to access this run")

    return await reject_run(run_id)


@router.patch("/run-status")
async def patch_run_status(
    request: RunStatusUpdate,
    user: Annotated[User, Depends(get_current_user)] = None
) -> RunInDB:

    if not user or not await user_owns_runs(user.id, [request.run_id]):
        raise HTTPException(
            status_code=403, detail="You do not have permission to access this run")

    run = await update_run_status(request.run_id, request)
    return run


@router.post("/run-message")
async def post_run_message(
    request: RunMessageCreate,
    user: Annotated[User, Depends(get_current_user)] = None
) -> RunMessageInDB:

    if not user or not await user_owns_runs(user.id, [request.run_id]):
        raise HTTPException(
            status_code=403, detail="You do not have permission to access this run")

    run_message = await create_run_message(request)
    return run_message


@router.post("/run-message-pydantic")
async def post_run_message_pydantic(
    request: RunMessageCreatePydantic,
    user: Annotated[User, Depends(get_current_user)] = None
) -> RunPydanticMessageInDB:

    if not user or not await user_owns_runs(user.id, [request.run_id]):
        raise HTTPException(
            status_code=403, detail="You do not have permission to access this run")

    run_message = await create_run_message_pydantic(request)
    return run_message


@router.get("/messages/{run_id}")
async def fetch_run_messages(
    run_id: uuid.UUID,
    user: Annotated[User, Depends(get_current_user)] = None,
) -> List[RunMessageInDB]:

    if not user or not await user_owns_runs(user.id, [run_id]):
        raise HTTPException(
            status_code=403, detail="You do not have permission to access this run")

    messages = await get_run_messages(run_id)
    return messages


@router.get("/messages-pydantic/{run_id}")
async def fetch_run_messages_pydantic(
    run_id: uuid.UUID,
    user: Annotated[User, Depends(get_current_user)] = None,
) -> List[RunPydanticMessageInDB]:

    if not user or not await user_owns_runs(user.id, [run_id]):
        raise HTTPException(
            status_code=403, detail="You do not have permission to access this run")

    run = await get_run_messages_pydantic(run_id, bytes=False)
    return run


@router.get("/stream-messages")
async def stream_run_messages(
    run_ids: Optional[List[uuid.UUID]] = None,
    project_id: Optional[uuid.UUID] = None,
    cache: Annotated[redis.Redis, Depends(get_redis)] = None,
    user: Annotated[User, Depends(get_current_user)] = None,
) -> StreamingResponse:

    runs = await get_runs(user.id, run_ids=run_ids, project_id=project_id)

    if not user or not await user_owns_runs(user.id, [run.id for run in runs]):
        raise HTTPException(
            status_code=403, detail="You do not have permission to access this run")

    elif not runs:
        raise HTTPException(
            status_code=404, detail="Runs not found")

    elif not any(run.status != "completed" for run in runs):
        return Response(content="All runs are completed.", media_type="text/plain")

    # Default timeout of 30 seconds
    timeout = 30
    timeout = min(timeout, SSE_MAX_TIMEOUT)
    stream_keys = [str(run.id) for run in runs]

    async def stream_run_updates():
        # Track last_id for each stream
        last_ids = {key: "$" for key in stream_keys}
        start_time = time.time()

        while True:
            response = await cache.xread(last_ids, count=10, block=int(SSE_MIN_SLEEP_TIME * 1000))

            from pprint import pprint
            pprint(response)

            if response:
                start_time = time.time()
                # XREAD returns: [[stream_name, [[msg_id, {fields}], ...]], ...]
                for stream_key, messages in response:
                    for message_id, message_data in messages:
                        last_ids[stream_key] = message_id

                        message_validated = RunMessageCreate(**message_data)
                        output_data = RunMessageInDB(
                            id=uuid.uuid4(),
                            content=message_validated.content,
                            run_id=stream_key,
                            type=message_validated.type,
                            created_at=datetime.now(timezone.utc)
                        )
                        yield f"data: {output_data.model_dump_json(by_alias=True)}\n\n"

            if start_time + timeout < time.time():
                break

    return StreamingResponse(stream_run_updates(), media_type="text/event-stream")


@router.get("/stream-incomplete-runs")
async def stream_incomplete_runs(
    project_id: Optional[uuid.UUID] = None,
    user: Annotated[User, Depends(get_current_user)] = None
) -> StreamingResponse:

    adapter = TypeAdapter(List[Run])

    async def stream_incomplete_runs():
        prev_run_ids = []
        while True:
            incomplete_runs = await get_runs(user.id, filter_status=["running", "pending"], project_id=project_id)

            # Include recently stopped runs to ensure we don't miss the associated state changes
            # Could optionally listen for when a run id is removed from this list in the frontend, then mutate all jobs, but this is more efficient
            stopped_run_ids = [
                run_id for run_id in prev_run_ids if run_id not in [run.id for run in incomplete_runs]]

            stopped_runs = await get_runs(user.id, run_ids=stopped_run_ids, project_id=project_id)
            runs = stopped_runs + incomplete_runs
            yield f"data: {adapter.dump_json(runs, by_alias=True).decode("utf-8")}\n\n"
            prev_run_ids = [run.id for run in runs]

            await asyncio.sleep(SSE_MIN_SLEEP_TIME)

    return StreamingResponse(stream_incomplete_runs(), media_type="text/event-stream")
