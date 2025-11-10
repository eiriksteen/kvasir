import uuid
from datetime import datetime, timezone
from typing import List, Optional
from sqlalchemy import insert, select, update
from fastapi import HTTPException

from synesis_schemas.main_server import (
    DataSourceInDB,
    FileDataSourceInDB,
    DataSource,
    DataSourceCreate,
    DataSourceDetailsCreate,
    UnknownFileCreate,
)
from synesis_api.modules.data_sources.models import (
    file_data_source,
    data_source,
)
from synesis_api.database.service import execute, fetch_all


async def create_data_source(
        user_id: uuid.UUID,
        data_source_create: DataSourceCreate) -> DataSource:

    # Get the fields defined in DataSourceCreate (excluding type_fields and from_pipelines)
    extra_fields = data_source_create.model_extra or {}

    # Handle additional variables - only if type_fields is provided
    additional_variables = {**extra_fields}
    if data_source_create.type_fields:
        extra_type_fields = data_source_create.type_fields.model_extra or {}
        # We also add all fields present in type fields and not present in unknown file create into the additional variables
        file_type_fields = {k: v for k, v in data_source_create.type_fields.model_dump().items()
                            if k not in UnknownFileCreate.model_fields}
        additional_variables = {**extra_fields,
                                **extra_type_fields,
                                **file_type_fields}

    # Create the base data source
    data_source_id = uuid.uuid4()
    data_source_obj = DataSourceInDB(
        id=data_source_id,
        user_id=user_id,
        **data_source_create.model_dump(exclude=list(extra_fields.keys())),
        additional_variables=additional_variables,
        created_at=datetime.now(timezone.utc)
    )

    await execute(
        insert(data_source).values(data_source_obj.model_dump()),
        commit_after=True
    )

    # Handle type-specific fields
    type_fields = data_source_create.type_fields
    if type_fields:
        if data_source_create.type == "file":
            # Insert into file_data_source table
            file_data_source_obj = FileDataSourceInDB(
                id=data_source_id,
                **type_fields.model_dump(),
                created_at=datetime.now(timezone.utc),
                updated_at=datetime.now(timezone.utc)
            )
            await execute(
                insert(file_data_source).values(
                    file_data_source_obj.model_dump()),
                commit_after=True
            )

    # from_pipelines edges are now managed by project_graph module

    return (await get_user_data_sources(user_id, [data_source_id]))[0]


async def add_data_source_details(
        user_id: uuid.UUID,
        details_create: DataSourceDetailsCreate) -> DataSource:
    # First verify the data source exists and belongs to the user
    existing = await get_user_data_sources(user_id, [details_create.data_source_id])
    if not existing:
        raise HTTPException(status_code=404, detail="Data source not found")

    data_source_obj = existing[0]

    # Check if details already exist
    if data_source_obj.type_fields is not None:
        raise HTTPException(
            status_code=400, detail="Data source details already exist")

    # Extract additional variables from type_fields
    extra_type_fields = details_create.type_fields.model_extra or {}
    file_type_fields = {k: v for k, v in details_create.type_fields.model_dump().items()
                        if k not in UnknownFileCreate.model_fields}

    new_additional_variables = {
        **(data_source_obj.additional_variables or {}),
        **extra_type_fields,
        **file_type_fields
    }

    # Update the base data source with additional variables
    await execute(
        update(data_source)
        .where(data_source.c.id == details_create.data_source_id)
        .values(additional_variables=new_additional_variables),
        commit_after=True
    )

    # Insert type-specific fields
    if data_source_obj.type == "file":
        file_data_source_obj = FileDataSourceInDB(
            id=details_create.data_source_id,
            **details_create.type_fields.model_dump(),
            created_at=datetime.now(timezone.utc),
            updated_at=datetime.now(timezone.utc)
        )
        await execute(
            insert(file_data_source).values(file_data_source_obj.model_dump()),
            commit_after=True
        )

    return (await get_user_data_sources(user_id, [details_create.data_source_id]))[0]


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

    if not source_records:
        return []

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

        output_records.append(DataSource(
            **source_obj.model_dump(),
            type_fields=type_fields_obj
        ))

    return output_records
