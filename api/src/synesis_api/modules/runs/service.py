import uuid
from datetime import datetime, timezone
from typing import Literal, Optional, List
from sqlalchemy import select, insert, delete
from pydantic_ai.messages import ModelMessage, ModelMessagesTypeAdapter
from synesis_api.database.service import fetch_all, execute, fetch_one
from synesis_api.modules.runs.schema import (
    RunInDB,
    RunPydanticMessageInDB,
    RunMessageInDB,
    DataIntegrationRunInputInDB,
    DataIntegrationRunResultInDB,
    DataIntegrationRunInput,
    DataSourceInRunInDB,
    ModelIntegrationRunResultInDB,
)
from synesis_api.modules.runs.models import (
    run,
    run_pydantic_message,
    run_message,
    data_integration_run_result,
    data_integration_run_input,
    data_source_in_run,
    model_integration_run_result
)
from synesis_api.modules.data_sources.service import get_data_sources_by_ids


async def create_run(
        conversation_id: uuid.UUID,
        user_id: uuid.UUID,
        type: Literal["chat", "data_integration", "analysis", "automation"],
        run_id: Optional[uuid.UUID] = None,
        context_id: Optional[uuid.UUID] = None,
        run_name: Optional[str] = None) -> RunInDB:

    run_record = RunInDB(
        id=run_id if run_id else uuid.uuid4(),
        conversation_id=conversation_id,
        type=type,
        context_id=context_id,
        user_id=user_id,
        run_name=run_name,
        started_at=datetime.now(timezone.utc),
        status="running"
    )

    await execute(run.insert().values(run_record.model_dump()), commit_after=True)

    return run_record


async def get_run(run_id: uuid.UUID) -> RunInDB:
    run_record = await fetch_one(
        select(run).where(run.c.id == run_id)
    )
    return RunInDB(**run_record)


async def get_runs(user_id: uuid.UUID) -> List[RunInDB]:
    runs = await fetch_all(
        select(run).where(run.c.user_id == user_id)
    )

    return [RunInDB(**run_record) for run_record in runs]


async def get_incomplete_runs(user_id: uuid.UUID) -> List[RunInDB]:
    runs = await fetch_all(
        select(run).where(run.c.user_id == user_id).where(
            run.c.status.not_in_(["completed", "failed"]))
    )
    return [RunInDB(**run_record) for run_record in runs]


async def get_runs_by_ids(run_ids: List[uuid.UUID]) -> List[RunInDB]:
    runs = await fetch_all(
        select(run).where(run.c.id.in_(run_ids))
    )
    return [RunInDB(**run_record) for run_record in runs]


async def update_run_status(run_id: uuid.UUID, status: Literal["running", "completed", "failed"]) -> RunInDB:
    run_record = RunInDB(**(await fetch_one(
        select(run).where(run.c.id == run_id)
    )))
    run_record.status = status
    await execute(run.update().where(run.c.id == run_id).values(status=status), commit_after=True)
    return run_record


async def get_run_messages_pydantic(run_id: uuid.UUID) -> list[ModelMessage]:
    c = await fetch_all(
        select(run_pydantic_message).where(
            run_pydantic_message.c.run_id == run_id)
    )
    messages: list[ModelMessage] = []
    for message in c:
        messages.extend(
            ModelMessagesTypeAdapter.validate_json(message["message_list"]))

    return messages


async def create_run_message(
        type: Literal["tool_call", "result", "error"],
        run_id: uuid.UUID,
        content: str) -> RunMessageInDB:

    run_message_record = RunMessageInDB(
        id=uuid.uuid4(),
        content=content,
        type=type,
        run_id=run_id,
        created_at=datetime.now(timezone.utc)
    )

    await execute(run_message.insert().values(run_message_record.model_dump()), commit_after=True)

    return run_message_record


async def create_run_message_pydantic(run_id: uuid.UUID, messages: bytes) -> RunPydanticMessageInDB:
    run_pydantic_message_record = RunPydanticMessageInDB(
        id=uuid.uuid4(),
        run_id=run_id,
        message_list=messages,
        created_at=datetime.now(timezone.utc)
    )

    await execute(run_pydantic_message.insert().values(run_pydantic_message_record.model_dump()), commit_after=True)

    return run_pydantic_message_record


async def create_data_integration_run_result(run_id: uuid.UUID, dataset_id: uuid.UUID, code_explanation: str, python_code_path: str):

    result = DataIntegrationRunResultInDB(
        run_id=run_id,
        dataset_id=dataset_id,
        code_explanation=code_explanation,
        python_code_path=python_code_path
    )

    await execute(
        insert(data_integration_run_result).values(result.model_dump()), commit_after=True
    )


async def delete_data_integration_run_result(run_id: uuid.UUID):
    await execute(
        delete(data_integration_run_result).where(
            data_integration_run_result.c.run_id == run_id),
        commit_after=True
    )


async def create_data_integration_run_input(run_id: uuid.UUID, target_data_description: str, data_source_ids: List[uuid.UUID]):
    # Create the run input record
    run_input = DataIntegrationRunInputInDB(
        run_id=run_id,
        target_dataset_description=target_data_description,
        created_at=datetime.now(timezone.utc),
        updated_at=datetime.now(timezone.utc)
    )

    await execute(
        insert(data_integration_run_input).values(run_input.model_dump()),
        commit_after=True
    )

    # Create the data source associations
    data_source_associations = [
        DataSourceInRunInDB(
            run_id=run_id,
            data_source_id=data_source_id,
            created_at=datetime.now(timezone.utc),
        ).model_dump() for data_source_id in data_source_ids
    ]

    await execute(
        insert(data_source_in_run).values(
            data_source_associations),
        commit_after=True
    )


async def get_data_integration_run_input(run_id: uuid.UUID) -> DataIntegrationRunInput:
    # Get the run input record
    run_input = await fetch_one(
        select(data_integration_run_input).where(
            data_integration_run_input.c.run_id == run_id),
        commit_after=True
    )

    # Get the associated data source IDs
    data_source_associations = await fetch_all(
        select(data_source_in_run).where(
            data_source_in_run.c.run_id == run_id),
        commit_after=True
    )

    data_source_ids = [assoc["data_source_id"]
                       for assoc in data_source_associations]

    # Get the full data sources
    data_sources = await get_data_sources_by_ids(data_source_ids)

    return DataIntegrationRunInput(
        run_id=run_input["run_id"],
        target_dataset_description=run_input["target_dataset_description"],
        created_at=run_input["created_at"],
        data_sources=data_sources
    )


async def create_model_integration_run_result(run_id: uuid.UUID, model_id: uuid.UUID):

    result = ModelIntegrationRunResultInDB(
        run_id=run_id,
        model_id=model_id
    )

    await execute(
        insert(model_integration_run_result).values(
            result.model_dump()),
        commit_after=True
    )


async def get_model_integration_run_results(run_id: uuid.UUID) -> ModelIntegrationRunResultInDB:
    # get results from model_integration_run_results
    results = await fetch_one(
        select(model_integration_run_result).where(
            model_integration_run_result.c.run_id == run_id),
        commit_after=True
    )

    return ModelIntegrationRunResultInDB(**results)
