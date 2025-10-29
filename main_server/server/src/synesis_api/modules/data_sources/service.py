import uuid
from datetime import datetime, timezone
from typing import List, Optional
from sqlalchemy import insert, select, update

from synesis_api.modules.data_sources.description import get_data_source_description
from synesis_schemas.main_server import (
    DataSourceInDB,
    FileDataSourceInDB,
    DataSource,
    DataSourceCreate,
    FileDataSourceCreate,
)
from synesis_api.modules.data_sources.models import (
    file_data_source,
    data_source,
)
from synesis_api.database.service import execute, fetch_all


async def create_data_source(
        user_id: uuid.UUID,
        data_source_create: DataSourceCreate) -> DataSource:

    # Extract additional variables from the create request
    create_data = data_source_create.model_dump()
    additional_variables = {}

    # Get the fields defined in DataSourceCreate
    create_fields = set(DataSourceCreate.model_fields.keys())
    for key, value in create_data.items():
        if key not in create_fields:
            additional_variables[key] = value

    data_source_obj = DataSourceInDB(
        id=uuid.uuid4(),
        user_id=user_id,
        **{k: v for k, v in create_data.items() if k in create_fields},
        additional_variables=additional_variables if additional_variables else None,
        created_at=datetime.now(timezone.utc)
    )

    await execute(
        insert(data_source).values(data_source_obj.model_dump()),
        commit_after=True
    )

    return (await get_user_data_sources(user_id, [data_source_obj.id]))[0]


async def create_file_data_source(
        user_id: uuid.UUID,
        data_source_create: FileDataSourceCreate,
        data_source_id: Optional[uuid.UUID] = None) -> DataSource:

    # Extract additional variables from the create request
    create_data = data_source_create.model_dump()
    additional_variables = {}

    # Get the fields defined in FileDataSourceCreate
    create_fields = set(FileDataSourceCreate.model_fields.keys())
    for key, value in create_data.items():
        if key not in create_fields:
            additional_variables[key] = value

    if not data_source_id:
        # Create new data source
        data_source_id = uuid.uuid4()
        data_source_obj = DataSourceInDB(
            id=data_source_id,
            user_id=user_id,
            type="file",
            **{k: v for k, v in create_data.items() if k in create_fields},
            additional_variables=additional_variables if additional_variables else None,
            created_at=datetime.now(timezone.utc)
        )

        await execute(
            insert(data_source).values(data_source_obj.model_dump()),
            commit_after=True
        )
    elif additional_variables:
        existing_query = select(data_source.c.additional_variables).where(
            data_source.c.id == data_source_id)
        existing_result = await fetch_all(existing_query)
        if existing_result:
            existing_additional_variables = existing_result[0]["additional_variables"]
            additional_variables = {
                **(existing_additional_variables or {}), **additional_variables}

        await execute(
            update(data_source)
            .where(data_source.c.id == data_source_id)
            .values(additional_variables=additional_variables),
            commit_after=True
        )

    file_data_source_obj = FileDataSourceInDB(
        id=data_source_id,
        **create_data,
        created_at=datetime.now(timezone.utc),
        updated_at=datetime.now(timezone.utc)
    )

    await execute(
        insert(file_data_source).values(
            file_data_source_obj.model_dump()),
        commit_after=True
    )

    return (await get_user_data_sources(user_id, [data_source_id]))[0]


async def get_user_data_sources(user_id: uuid.UUID, data_source_ids: Optional[List[uuid.UUID]] = None) -> List[DataSource]:
    """Get data sources by user ID, returning the most specific type"""
    # Get the base data source
    data_source_query = select(data_source).where(
        data_source.c.user_id == user_id
    )
    if data_source_ids is not None:
        data_source_query = data_source_query.where(
            data_source.c.id.in_(data_source_ids)
        )

    source_records = await fetch_all(data_source_query)
    source_ids = [record["id"] for record in source_records]

    # Get file data source records
    file_source_query = select(file_data_source).where(
        file_data_source.c.id.in_(source_ids)
    )
    file_source_records = await fetch_all(file_source_query)

    output_records = []
    for source_id in source_ids:
        source_obj = DataSourceInDB(**next(
            iter([record for record in source_records if record["id"] == source_id])))

        file_record = next(
            iter([record for record in file_source_records if record["id"] == source_id]), None)

        type_fields_obj = None
        if file_record:
            type_fields_obj = FileDataSourceInDB(**file_record)

        description = get_data_source_description(source_obj, type_fields_obj)

        output_records.append(DataSource(
            **source_obj.model_dump(),
            type_fields=type_fields_obj,
            description_for_agent=description
        ))

    return output_records
