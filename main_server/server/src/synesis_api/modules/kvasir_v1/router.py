import uuid
import time
import redis
import asyncio
from datetime import datetime, timezone
from pprint import pprint
from fastapi import APIRouter, Depends, HTTPException
from fastapi.responses import StreamingResponse, Response
from typing import Annotated, List, Optional
from pydantic import TypeAdapter
from sqlalchemy import insert

from synesis_api.auth.service import get_current_user, user_owns_runs, oauth2_scheme
from synesis_api.auth.schema import User
from synesis_api.redis import get_redis
from synesis_api.app_secrets import SSE_MAX_TIMEOUT, SSE_MIN_SLEEP_TIME
from synesis_api.modules.kvasir_v1.callbacks import ApplicationCallbacks
from synesis_api.modules.kvasir_v1.models import message
from synesis_api.database.service import execute
from synesis_api.modules.entity_graph.service import EntityGraphs
from kvasir_research.agents.v1.kvasir.agent import KvasirV1
from synesis_api.utils.pydanticai_utils import helper_agent
from kvasir_research.agents.v1.data_model import (
    Message,
    MessageCreate,
    RunBase,
    RunCreate,
)

# Create a single instance for router use
_callbacks = ApplicationCallbacks()

router = APIRouter()


@router.post("/completions")
async def post_chat(
    prompt: MessageCreate,
    user: Annotated[User, Depends(get_current_user)] = None,
    token: str = Depends(oauth2_scheme)
) -> StreamingResponse:

    # TODO: Add support for open connection with analysis, and add rejected status to a run so we don't keep monitoring it

    run_records = await _callbacks.get_runs(user.id, run_id=prompt.run_id)
    if not run_records:
        raise HTTPException(
            status_code=404, detail="Run not found")

    run_record = run_records[0]

    if run_record.user_id != user.id:
        raise HTTPException(
            status_code=403, detail="You do not have access to this run")

    if not run_record.type == "kvasir":
        raise HTTPException(
            status_code=400, detail="Run is not a Kvasir run")

    graph_service = EntityGraphs(user.id)
    node_group = await graph_service.get_node_group(run_record.project_id)
    if not node_group:
        raise HTTPException(
            status_code=404, detail="Project not found")

    messages = await _callbacks.get_messages(user.id, run_record.id)
    is_new_conversation = len(messages) == 0

    # Create user message
    user_message = Message(
        id=uuid.uuid4(),
        run_id=prompt.run_id,
        content=prompt.content,
        role=prompt.role,
        type=prompt.type,
        created_at=datetime.now(timezone.utc)
    )
    await execute(insert(message).values(**user_message.model_dump()), commit_after=True)

    agent = KvasirV1(
        user_id=user.id,
        run_id=run_record.id,
        project_id=run_record.project_id,
        package_name=node_group.python_package_name,
        sandbox_type="modal",
        callbacks=ApplicationCallbacks(),
        bearer_token=token
    )

    async def stream_response():
        response_message = Message(
            id=uuid.uuid4(),
            run_id=run_record.id,
            role="kvasir",
            type="chat",
            content="",
            created_at=datetime.now(timezone.utc)
        )

        prev_response_text = ""
        async for kvasir_v1_output, is_last in agent(prompt.content):
            if kvasir_v1_output != prev_response_text:
                response_message.content = kvasir_v1_output.response
                yield f"data: {response_message.model_dump_json(by_alias=True)}\n\n"
            if is_last:
                # Multiple messages can be streamed in one go
                await _callbacks.create_message(user.id, MessageCreate(
                    run_id=run_record.id,
                    type="chat",
                    content=response_message.content,
                    role="kvasir"
                ))
                response_message = Message(
                    id=uuid.uuid4(),
                    run_id=run_record.id,
                    role="kvasir",
                    type="chat",
                    content="",
                    created_at=datetime.now(timezone.utc)
                )

                prev_response_text = ""

        if is_new_conversation:
            name = await helper_agent.run(
                f"The user wants to start a new conversation. The user has written this: '{prompt.content}'.\n\n" +
                "What is the name of the conversation? Just give me the name of the conversation, no other text.\n\n" +
                "NB: Do not output a response to the prompt, that is done elsewhere! Just produce a suitable topic name given the prompt.",
                output_type=str
            )
            name = name.output.replace(
                '"', '').replace("'", "").strip()

            await _callbacks.update_run_name(user.id, run_record.id, name)

        success_message = Message(
            id=uuid.uuid4(),
            run_id=run_record.id,
            role="kvasir",
            type="result",
            content="DONE",
            created_at=datetime.now(timezone.utc)
        )

        yield f"data: {success_message.model_dump_json(by_alias=True)}\n\n"

        await asyncio.sleep(SSE_MIN_SLEEP_TIME)

    return StreamingResponse(stream_response(), media_type="text/event-stream")


@router.post("/run", response_model=RunBase)
async def post_user_run(run_data: RunCreate, user: Annotated[User, Depends(get_current_user)] = None) -> RunBase:
    return await _callbacks.create_run(user.id, run_data)


@router.get("/runs")
async def fetch_runs(
    project_id: Optional[uuid.UUID] = None,
    user: Annotated[User, Depends(get_current_user)] = None
) -> List[RunBase]:
    runs = await _callbacks.get_runs(user.id, project_id=project_id)
    return runs


@router.get("/messages/{run_id}")
async def fetch_run_messages(
    run_id: uuid.UUID,
    user: Annotated[User, Depends(get_current_user)] = None,
) -> List[Message]:

    if not user or not await user_owns_runs(user.id, [run_id]):
        raise HTTPException(
            status_code=403, detail="You do not have permission to access this run")

    messages = await _callbacks.get_messages(user.id, run_id)
    return messages


@router.get("/stream-messages")
async def stream_run_messages(
    run_ids: Optional[List[uuid.UUID]] = None,
    project_id: Optional[uuid.UUID] = None,
    cache: Annotated[redis.Redis, Depends(get_redis)] = None,
    user: Annotated[User, Depends(get_current_user)] = None,
) -> StreamingResponse:

    runs = await _callbacks.get_runs(user.id, run_ids=run_ids, project_id=project_id)

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

            if response:
                start_time = time.time()
                # XREAD returns: [[stream_name, [[msg_id, {fields}], ...]], ...]
                for stream_key, messages in response:
                    for message_id, message_data in messages:
                        last_ids[stream_key] = message_id

                        message_validated = MessageCreate(**message_data)
                        output_data = Message(
                            id=uuid.uuid4(),
                            content=message_validated.content,
                            run_id=uuid.UUID(stream_key),
                            type=message_validated.type,
                            role=message_validated.role,
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

    adapter = TypeAdapter(List[RunBase])

    async def stream_incomplete_runs():
        prev_run_ids = []
        while True:
            incomplete_runs = await _callbacks.get_runs(user.id, filter_status=["running", "pending"], project_id=project_id)

            # Include recently stopped runs to ensure we don't miss the associated state changes
            # Could optionally listen for when a run id is removed from this list in the frontend, then mutate all jobs, but this is more efficient
            stopped_run_ids = [
                run_id for run_id in prev_run_ids if run_id not in [run.id for run in incomplete_runs]]

            stopped_runs = await _callbacks.get_runs(user.id, run_ids=stopped_run_ids, project_id=project_id)
            runs = stopped_runs + incomplete_runs
            yield f"data: {adapter.dump_json(runs, by_alias=True).decode("utf-8")}\n\n"
            prev_run_ids = [run.id for run in runs]

            await asyncio.sleep(SSE_MIN_SLEEP_TIME)

    return StreamingResponse(stream_incomplete_runs(), media_type="text/event-stream")
