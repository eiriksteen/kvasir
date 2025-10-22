import uuid
from datetime import datetime, timezone
from typing import List, Optional
from sqlalchemy import insert, select
from fastapi import HTTPException

from synesis_api.modules.data_sources.description import get_data_source_description
from synesis_schemas.main_server import (
    DataSourceInDB,
    TabularFileDataSourceInDB,
    DataSourceAnalysisInDB,
    DataSource,
    TabularFileDataSourceCreate,
    DataSourceAnalysisCreate,
    KeyValueFileDataSourceCreate,
    KeyValueFileDataSourceInDB,
)
from synesis_api.modules.data_sources.models import (
    tabular_file_data_source,
    data_source,
    data_source_analysis,
    key_value_file_data_source,
)
from synesis_api.database.service import execute, fetch_all


async def create_tabular_file_data_source(
        user_id: uuid.UUID,
        data_source_create: TabularFileDataSourceCreate) -> DataSource:

    data_source_obj = DataSourceInDB(
        id=uuid.uuid4(),
        user_id=user_id,
        type="tabular_file",
        **data_source_create.model_dump(),
        created_at=datetime.now()
    )

    tabular_data_source_obj = TabularFileDataSourceInDB(
        id=data_source_obj.id,
        **data_source_create.model_dump(),
        created_at=datetime.now(timezone.utc),
        updated_at=datetime.now(timezone.utc)
    )

    await execute(
        insert(data_source).values(data_source_obj.model_dump()),
        commit_after=True
    )

    await execute(
        insert(tabular_file_data_source).values(
            tabular_data_source_obj.model_dump()),
        commit_after=True
    )

    return (await get_user_data_sources(user_id, [data_source_obj.id]))[0]


async def create_key_value_data_source(
        user_id: uuid.UUID,
        data_source_create: KeyValueFileDataSourceCreate) -> DataSource:
    # TODO: deal with features

    data_source_obj = DataSourceInDB(
        id=uuid.uuid4(),
        user_id=user_id,
        type="key_value_file",
        **data_source_create.model_dump(),
        created_at=datetime.now()
    )

    key_value_data_source_obj = KeyValueFileDataSourceInDB(
        id=data_source_obj.id,
        **data_source_create.model_dump(),
        created_at=datetime.now(timezone.utc),
        updated_at=datetime.now(timezone.utc)
    )

    await execute(
        insert(data_source).values(data_source_obj.model_dump()),
        commit_after=True
    )

    await execute(
        insert(key_value_file_data_source).values(
            key_value_data_source_obj.model_dump()),
        commit_after=True
    )

    return (await get_user_data_sources(user_id, [data_source_obj.id]))[0]


async def create_data_source_analysis(analysis: DataSourceAnalysisCreate) -> DataSourceAnalysisInDB:

    analysis_record = DataSourceAnalysisInDB(
        id=analysis.data_source_id,
        created_at=datetime.now(timezone.utc),
        updated_at=datetime.now(timezone.utc),
        **analysis.model_dump()
    )

    await execute(
        insert(data_source_analysis).values(analysis_record.model_dump()),
        commit_after=True
    )

    return analysis_record


async def get_user_data_sources(user_id: uuid.UUID, data_source_ids: Optional[List[uuid.UUID]] = None) -> List[DataSource]:
    """Get a data source by ID, returning the most specific type"""
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

    # Tabular source record

    tabular_source_query = select(tabular_file_data_source).where(
        tabular_file_data_source.c.id.in_(source_ids)
    )
    tabular_source_records = await fetch_all(tabular_source_query)

    # Key value source record

    key_value_source_query = select(key_value_file_data_source).where(
        key_value_file_data_source.c.id.in_(source_ids)
    )
    key_value_source_records = await fetch_all(key_value_source_query)

    # Analysis record

    analysis_query = select(data_source_analysis).where(
        data_source_analysis.c.id.in_(source_ids)
    )
    analysis_records = await fetch_all(analysis_query)

    output_records = []
    for source_id in source_ids:
        source_obj = DataSourceInDB(**next(
            iter([record for record in source_records if record["id"] == source_id])))

        tabular_record = next(
            iter([record for record in tabular_source_records if record["id"] == source_id]), None)

        key_value_record = next(
            iter([record for record in key_value_source_records if record["id"] == source_id]), None)

        type_fields_obj = None
        if tabular_record:
            tabular_obj = TabularFileDataSourceInDB(**tabular_record)
            type_fields_obj = TabularFileDataSourceInDB(
                **tabular_obj.model_dump())
        elif key_value_record:
            key_value_obj = KeyValueFileDataSourceInDB(**key_value_record)
            type_fields_obj = KeyValueFileDataSourceInDB(
                **key_value_obj.model_dump())
        else:
            raise HTTPException(
                status_code=500, detail="Incomplete data source record")

        analysis_record = next(
            iter([record for record in analysis_records if record["id"] == source_id]), None)

        analysis_obj = None
        if analysis_record:
            analysis_obj = DataSourceAnalysisInDB(**analysis_record)

        description = get_data_source_description(
            source_obj, type_fields_obj, analysis_obj)

        output_records.append(DataSource(
            **source_obj.model_dump(),
            type_fields=type_fields_obj,
            analysis=analysis_obj,
            description_for_agent=description
        ))

    return output_records
