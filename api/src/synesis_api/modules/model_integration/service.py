import uuid
from datetime import datetime, timezone
from sqlalchemy import insert, select, delete
from pydantic_ai.messages import ModelMessage, ModelMessagesTypeAdapter
from synesis_api.modules.model_integration.schema import ModelIntegrationJobResultInDB, ModelIntegrationPydanticMessage, ModelIntegrationMessage
from synesis_api.modules.model_integration.models import model_integration_jobs_results, model_integration_pydantic_message, model_integration_message
from synesis_api.database.service import execute, fetch_one, fetch_all
from synesis_api.redis import get_redis


async def create_model_integration_result(job_id: uuid.UUID, model_id: uuid.UUID):

    result = ModelIntegrationJobResultInDB(
        job_id=job_id,
        model_id=model_id
    )

    await execute(
        insert(model_integration_jobs_results).values(
            result.model_dump()),
        commit_after=True
    )


async def delete_model_integration_result(job_id: uuid.UUID):
    await execute(
        delete(model_integration_jobs_results).where(
            model_integration_jobs_results.c.job_id == job_id),
        commit_after=True
    )


async def get_model_integration_job_results(job_id: uuid.UUID) -> ModelIntegrationJobResultInDB:
    # get results from model_integration_jobs_results
    results = await fetch_one(
        select(model_integration_jobs_results).where(
            model_integration_jobs_results.c.job_id == job_id),
        commit_after=True
    )

    return ModelIntegrationJobResultInDB(**results)


async def create_model_integration_messages_pydantic(job_id: uuid.UUID, messages: bytes) -> ModelIntegrationPydanticMessage:

    pydantic_message = ModelIntegrationPydanticMessage(
        id=uuid.uuid4(),
        job_id=job_id,
        message_list=messages,
        created_at=datetime.now(timezone.utc)
    )

    await execute(
        insert(model_integration_pydantic_message).values(
            pydantic_message.model_dump()),
        commit_after=True)

    return pydantic_message


async def get_model_integration_messages_pydantic(job_id: uuid.UUID) -> list[ModelMessage]:
    c = await fetch_all(
        select(model_integration_pydantic_message).where(
            model_integration_pydantic_message.c.job_id == job_id)
    )
    messages: list[ModelMessage] = []
    for message in c:
        messages.extend(
            ModelMessagesTypeAdapter.validate_json(message["message_list"]))

    return messages


async def get_model_id_from_job_id(job_id: uuid.UUID) -> uuid.UUID:
    model_id = await fetch_one(
        select(model_integration_jobs_results).where(
            model_integration_jobs_results.c.job_id == job_id),
        commit_after=True
    )

    return model_id["model_id"]


async def create_model_integration_messages(job_id: uuid.UUID, messages: list[dict]) -> list[ModelIntegrationMessage]:

    if messages:
        message_records = [
            ModelIntegrationMessage(
                id=message["id"],
                job_id=job_id,
                stage=message["stage"],
                created_at=message["timestamp"],
                content=message["content"],
                type=message["type"],
                current_task=message.get("current_task")
            )
            for message in messages
        ]

        await execute(
            insert(model_integration_message).values(
                [message.model_dump() for message in message_records]),
            commit_after=True
        )

        return message_records

    else:
        return []


async def get_model_integration_messages(job_id: uuid.UUID, include_cached: bool = True) -> list[ModelIntegrationMessage]:
    messages = await fetch_all(
        select(model_integration_message).where(
            model_integration_message.c.job_id == job_id
        )
    )

    messages = [ModelIntegrationMessage(**message) for message in messages]

    if include_cached:
        cache = get_redis()

        max_timestamp = max(
            [message.created_at for message in messages]) if messages else None

        response = await cache.xread({str(job_id): 0}, count=None)

        if response:
            cached_messages = [ModelIntegrationMessage(
                **item[1],
                job_id=job_id,
                created_at=datetime.fromisoformat(item[1]["timestamp"])
            ) for item in response[0][1] if item[1]["type"] != "pydantic_ai_state"]

            if max_timestamp:
                cached_messages = [
                    message for message in cached_messages if message.created_at > max_timestamp]
        else:
            cached_messages = []

        return messages + cached_messages
    else:
        return messages
