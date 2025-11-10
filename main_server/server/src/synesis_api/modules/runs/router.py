import sys
import uuid
import time
import redis
import asyncio
from datetime import datetime, timezone
from fastapi import APIRouter, Depends, HTTPException
from fastapi.responses import StreamingResponse, Response
from typing import Annotated, List
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
    RunInDB,
    StreamedCode
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
async def fetch_runs(user: Annotated[User, Depends(get_current_user)] = None) -> List[Run]:
    runs = await get_runs(user.id)
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

    run = await get_run_messages(run_id)

    if not run:
        raise HTTPException(
            status_code=404, detail="Run not found")

    return run


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


@router.get("/stream-messages/{run_id}")
async def stream_run_messages(
    run_id: uuid.UUID,
    cache: Annotated[redis.Redis, Depends(get_redis)],
    user: Annotated[User, Depends(get_current_user)] = None,
) -> StreamingResponse:

    run = await get_runs(user.id, run_ids=[run_id])
    run = run[0]

    if not user or not await user_owns_runs(user.id, [run_id]):
        raise HTTPException(
            status_code=403, detail="You do not have permission to access this run")

    elif not run:
        raise HTTPException(
            status_code=404, detail="Run not found")

    elif run.status == "completed":
        return Response(content="Run is completed, see conversation for results.", media_type="text/plain")

    # Default timeout of 30 seconds
    timeout = 30
    timeout = min(timeout, SSE_MAX_TIMEOUT)

    async def stream_run_updates():
        response = await cache.xread({str(run_id): "$"}, count=1, block=timeout*1000)
        start_time = time.time()
        last_id = response[0][1][-1][0] if response else None

        while True:
            response = await cache.xread({str(run_id): last_id}, count=1)

            if response:
                start_time = time.time()
                last_id = response[0][1][-1][0]
                message = response[0][1][0][1]
                message_validated = RunMessageCreate(**message)
                # Converting to InDB to enable client to treat these as valid messages
                output_data = RunMessageInDB(
                    id=uuid.uuid4(),
                    content=message_validated.content,
                    run_id=run_id,
                    type=message_validated.type,
                    created_at=datetime.now(timezone.utc)
                )
                yield f"data: {output_data.model_dump_json(by_alias=True)}\n\n"

            if start_time + timeout < time.time():
                break

    return StreamingResponse(stream_run_updates(), media_type="text/event-stream")


@router.get("/stream-code/{run_id}")
async def stream_run_code(
    run_id: uuid.UUID,
    cache: Annotated[redis.Redis, Depends(get_redis)],
    user: Annotated[User, Depends(get_current_user)] = None,
) -> StreamingResponse:

    run = await get_runs(user.id, run_ids=[run_id])
    run = run[0]

    if not user or not await user_owns_runs(user.id, [run_id]):
        raise HTTPException(
            status_code=403, detail="You do not have permission to access this run")

    elif not run:
        raise HTTPException(
            status_code=404, detail="Run not found")

    elif run.status == "completed":
        return Response(content="Run is completed, see conversation for results.", media_type="text/plain")

    # Default timeout of 30 seconds
    timeout = 30
    timeout = min(timeout, SSE_MAX_TIMEOUT)

    adapter = TypeAdapter(List[StreamedCode])

    async def stream_code_updates():
        # On connection, we search through the code messages and send the most recent version of every script to the client
        # Then, we just stream the updates as they come in
        # New files should show up, and edits to existing files should replace them
        all_code_responses = await cache.xread({f"{run_id}-code": "$"}, count=None, block=timeout*1000)
        filename_to_most_recent_message = {}
        last_id = None
        for response_num, response in enumerate(all_code_responses):
            message = StreamedCode(**response[1][0][1])
            filename_to_most_recent_message[message.filename] = message
            if response_num == len(all_code_responses) - 1:
                last_id = response[0][1][-1][0]

        if len(filename_to_most_recent_message) > 0:
            yield f"data: {adapter.dump_json(list(filename_to_most_recent_message.values()), by_alias=True).decode("utf-8")}\n\n"

        start_time = time.time()
        while True:
            if last_id:
                response = await cache.xread({f"{run_id}-code": last_id}, count=1)
            else:
                response = await cache.xread({f"{run_id}-code": "$"}, count=1)

            if response:
                start_time = time.time()
                last_id = response[0][1][-1][0]
                message = StreamedCode(**response[0][1][0][1])
                yield f"data: {adapter.dump_json([message], by_alias=True).decode("utf-8")}\n\n"

            if start_time + timeout < time.time():
                break

    return StreamingResponse(stream_code_updates(), media_type="text/event-stream")


@router.get("/stream-incomplete-runs")
async def stream_incomplete_runs(user: Annotated[User, Depends(get_current_user)] = None) -> StreamingResponse:

    adapter = TypeAdapter(List[Run])

    async def stream_incomplete_runs():
        prev_run_ids = []
        while True:
            incomplete_runs = await get_runs(user.id, filter_status=["running", "pending"])

            # Include recently stopped runs to ensure we don't miss the associated state changes
            # Could optionally listen for when a run id is removed from this list in the frontend, then mutate all jobs, but this is more efficient
            stopped_run_ids = [
                run_id for run_id in prev_run_ids if run_id not in [run.id for run in incomplete_runs]]

            stopped_runs = await get_runs(user.id, run_ids=stopped_run_ids)

            runs = stopped_runs + incomplete_runs

            yield f"data: {adapter.dump_json(runs, by_alias=True).decode("utf-8")}\n\n"

            prev_run_ids = [run.id for run in runs]

            await asyncio.sleep(SSE_MIN_SLEEP_TIME)

    return StreamingResponse(stream_incomplete_runs(), media_type="text/event-stream")
