import uuid
import time
import redis
import asyncio
from fastapi import APIRouter, Depends, HTTPException
from fastapi.responses import StreamingResponse, Response
from typing import Annotated, List
from pydantic import TypeAdapter

from synesis_api.auth.service import get_current_user, user_owns_run
from synesis_api.auth.schema import User
from synesis_api.redis import get_redis
from synesis_api.secrets import SSE_MAX_TIMEOUT, SSE_MIN_SLEEP_TIME
from synesis_api.modules.runs.schema import RunInDB, RunMessageInDB
from synesis_api.modules.runs.service import get_run, get_runs, get_incomplete_runs, get_runs_by_ids


router = APIRouter()


@router.get("/messages/{run_id}")
async def get_run_message(
    run_id: uuid.UUID,
    cache: Annotated[redis.Redis, Depends(get_redis)],
    user: Annotated[User, Depends(get_current_user)] = None,
) -> StreamingResponse:

    run = await get_run(run_id)

    if not user or not await user_owns_run(user.id, run_id):
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
                data = response[0][1][0][1]
                data_validated = RunMessageInDB(**data)
                yield f"data: {data_validated.model_dump_json()}\n\n"

            if start_time + timeout < time.time():
                break

    return StreamingResponse(stream_run_updates(), media_type="text/event-stream")


@router.get("/runs")
async def fetch_runs(
    user: Annotated[User, Depends(get_current_user)] = None,
) -> List[RunInDB]:
    runs = await get_runs(user.id)
    return runs


@router.get("/stream-incomplete-runs")
async def stream_incomplete_runs(
    user: Annotated[User, Depends(get_current_user)] = None,
    sleep_time: int = SSE_MIN_SLEEP_TIME
) -> StreamingResponse:

    adapter = TypeAdapter(List[RunInDB])
    runs = await get_incomplete_runs(user.id)
    incomplete_run_ids = [run.id for run in runs]

    async def stream_incomplete_runs():
        while True:
            # Use by IDs since we want to know when a running job transitions state to completed
            runs = await get_runs_by_ids(incomplete_run_ids)
            yield f"data: {adapter.dump_json(runs, by_alias=True).decode("utf-8")}\n\n"
            await asyncio.sleep(sleep_time)

    return StreamingResponse(stream_incomplete_runs(), media_type="text/event-stream")
