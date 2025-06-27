import uuid
import pandas as pd
from datetime import datetime, timezone
from typing import List
from fastapi import HTTPException
from sqlalchemy import insert, select, delete
from pydantic_ai.messages import ModelMessage, ModelMessagesTypeAdapter
from synesis_api.modules.data_integration.schema import IntegrationJobResultInDB, IntegrationPydanticMessage, IntegrationJobLocalInput, IntegrationMessage
from synesis_api.modules.data_integration.models import integration_jobs_results, integration_pydantic_message, integration_jobs_local_inputs, integration_message
from synesis_api.database.service import execute, fetch_one, fetch_all
from synesis_api.redis import get_redis


async def create_integration_result(result: IntegrationJobResultInDB):
    await execute(
        insert(integration_jobs_results).values(
            result.model_dump()),
        commit_after=True
    )


async def delete_integration_result(job_id: uuid.UUID):
    await execute(
        delete(integration_jobs_results).where(
            integration_jobs_results.c.job_id == job_id),
        commit_after=True
    )


def validate_restructured_data(
        data: pd.DataFrame,
        metadata: pd.DataFrame,
        mapping_dict: dict,
        index_first_level: str,
        index_second_level: str | None
) -> tuple[pd.DataFrame, pd.DataFrame, dict]:

    print("THE DATA")
    print(data.head())
    print("THE METADATA")
    print(metadata.head())
    print("THE MAPPING DICT")
    print(mapping_dict)
    print("THE INDEX FIRST LEVEL")
    print(index_first_level)
    print("THE INDEX SECOND LEVEL")
    print(index_second_level)

    if index_first_level not in data.columns:
        raise HTTPException(
            status_code=400,
            detail=f"Invalid data: First level index column '{index_first_level}' not found in DataFrame"
        )

    if index_second_level:
        if index_second_level not in data.columns:
            raise HTTPException(
                status_code=400,
                detail=f"Invalid data: Second level index column '{index_second_level}' not found in DataFrame!"
            )
        data = data.set_index([index_first_level, index_second_level])
    else:
        data = data.set_index(index_first_level)

    # Check for empty dataframes
    if data.empty:
        raise HTTPException(
            status_code=400,
            detail="Data is empty, please check your data and try again"
        )

    try:
        metadata = metadata.set_index(index_first_level)
    except Exception as e:
        raise HTTPException(
            status_code=400,
            detail=f"Invalid metadata or index, the first level index is not present in the metadata, error: {e}"
        )

    first_level_indices_data = set(
        data.index.get_level_values(0).unique().tolist())
    first_level_indices_metadata = set(
        metadata.index.get_level_values(0).unique().tolist())

    len_metadata = len(first_level_indices_metadata)
    len_data = len(first_level_indices_data)
    len_intersection = len(
        first_level_indices_metadata.intersection(first_level_indices_data))

    if not len_metadata == len_data or not len_metadata == len_intersection:
        intersection_fraction = (
            len_intersection / len_metadata) if len_metadata > 0 else 0

        if intersection_fraction == 0:
            raise HTTPException(
                status_code=400,
                detail="No overlap between metadata and data, are you sure you set the right index?"
            )

        raise HTTPException(
            status_code=400,
            detail=f"Metadata index does not match data index, {intersection_fraction} of metadata is present in data"
        )

    return data, metadata, mapping_dict


async def get_job_results_from_job_id(job_id: uuid.UUID) -> IntegrationJobResultInDB:
    # get results from integration_jobs_results
    results = await fetch_one(
        select(integration_jobs_results).where(
            integration_jobs_results.c.job_id == job_id),
        commit_after=True
    )

    return IntegrationJobResultInDB(**results)


async def get_job_results_from_dataset_id(dataset_id: uuid.UUID) -> List[IntegrationJobResultInDB]:
    # get results from integration_jobs_results
    results = await fetch_all(
        select(integration_jobs_results).where(
            integration_jobs_results.c.dataset_id == dataset_id),
        commit_after=True
    )

    return [IntegrationJobResultInDB(**result) for result in results]


async def create_messages_pydantic(job_id: uuid.UUID, messages: bytes) -> IntegrationPydanticMessage:

    pydantic_message = IntegrationPydanticMessage(
        id=uuid.uuid4(),
        job_id=job_id,
        message_list=messages,
        created_at=datetime.now(timezone.utc)
    )

    await execute(
        insert(integration_pydantic_message).values(
            pydantic_message.model_dump()),
        commit_after=True)

    return pydantic_message


async def get_messages_pydantic(job_id: uuid.UUID) -> list[ModelMessage]:
    c = await fetch_all(
        select(integration_pydantic_message).where(
            integration_pydantic_message.c.job_id == job_id)
    )
    messages: list[ModelMessage] = []
    for message in c:
        messages.extend(
            ModelMessagesTypeAdapter.validate_json(message["message_list"]))

    return messages


async def create_integration_input(input: IntegrationJobLocalInput, data_source: str):

    if data_source == "local":
        await execute(
            insert(integration_jobs_local_inputs).values(
                input.model_dump()),
            commit_after=True
        )
    else:
        raise HTTPException(
            status_code=400,
            detail="Invalid data source, currently only local is supported"
        )


async def get_integration_input(job_id: uuid.UUID) -> IntegrationJobLocalInput:

    # Currently only local source is supported

    input = await fetch_one(
        select(integration_jobs_local_inputs).where(
            integration_jobs_local_inputs.c.job_id == job_id),
        commit_after=True
    )

    return IntegrationJobLocalInput(**input)


async def get_dataset_id_from_job_id(job_id: uuid.UUID) -> uuid.UUID:
    dataset_id = await fetch_one(
        select(integration_jobs_results).where(
            integration_jobs_results.c.job_id == job_id),
        commit_after=True
    )

    return dataset_id["dataset_id"]


async def create_integration_messages(job_id: uuid.UUID, messages: list[dict]) -> list[IntegrationMessage]:

    if messages:
        message_records = [
            IntegrationMessage(
                id=message["id"],
                job_id=job_id,
                created_at=message["timestamp"],
                role=message["role"],
                content=message["content"],
                type=message["type"]
            )
            for message in messages
        ]

        await execute(
            insert(integration_message).values(
                [message.model_dump() for message in message_records]),
            commit_after=True
        )

        return message_records

    else:
        return []


async def get_integration_messages(job_id: uuid.UUID, include_cached: bool = True) -> list[IntegrationMessage]:
    messages = await fetch_all(
        select(integration_message).where(
            integration_message.c.job_id == job_id
        )
    )

    messages = [IntegrationMessage(**message) for message in messages]

    if include_cached:
        cache = get_redis()

        max_timestamp = max(
            [message.created_at for message in messages]) if messages else None

        response = await cache.xread({str(job_id): 0}, count=None)

        if response:
            cached_messages = [IntegrationMessage(
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
