import uuid
from typing import List

from project_server.client import ProjectClient
from synesis_schemas.main_server import (
    RunCreate,
    RunMessageCreate,
    RunMessageCreatePydantic,
    RunStatusUpdate,
    RunInDB,
    RunMessageInDB,
    Run,
    RunPydanticMessageInDB
)


async def post_run(client: ProjectClient, run: RunCreate) -> RunInDB:
    response = await client.send_request("post", "/runs/run", json=run.model_dump(mode="json"))
    return RunInDB(**response.body)


async def post_run_message(client: ProjectClient, run_message: RunMessageCreate) -> RunMessageInDB:
    response = await client.send_request("post", "/runs/run-message", json=run_message.model_dump(mode="json"))
    return RunMessageInDB(**response.body)


async def post_run_message_pydantic(client: ProjectClient, run_message: RunMessageCreatePydantic) -> RunPydanticMessageInDB:
    response = await client.send_request("post", "/runs/run-message-pydantic", json=run_message.model_dump(mode="json"))
    return RunPydanticMessageInDB(**response.body)


async def patch_run_status(client: ProjectClient, run_status: RunStatusUpdate):
    response = await client.send_request("patch", "/runs/run-status", json=run_status.model_dump(mode="json"))
    return RunInDB(**response.body)


async def get_runs(client: ProjectClient, exclude_swe: bool = True) -> List[Run]:
    response = await client.send_request("get", f"/runs/runs?exclude_swe={exclude_swe}")
    return [Run(**run) for run in response.body]


async def get_run_messages(client: ProjectClient, run_id: uuid.UUID) -> List[RunMessageInDB]:
    response = await client.send_request("get", f"/runs/messages/{run_id}")
    return [RunMessageInDB(**msg) for msg in response.body]


async def get_run_messages_pydantic(client: ProjectClient, run_id: uuid.UUID) -> List[RunPydanticMessageInDB]:
    response = await client.send_request("get", f"/runs/messages-pydantic/{run_id}")
    return [RunPydanticMessageInDB(**msg) for msg in response.body]
