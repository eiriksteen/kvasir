import uuid
from datetime import datetime, timezone
from typing import List, Optional, Union
from sqlalchemy import insert, select

from synesis_api.modules.data_sources.description import get_data_source_description
from synesis_schemas.main_server import FeatureInDB
from synesis_schemas.main_server import (
    DataSourceInDB,
    TabularFileDataSourceInDB,
    DataSourceAnalysisInDB,
    DataSource,
    TabularFileDataSource,
)
from synesis_api.modules.data_sources.models import (
    tabular_file_data_source,
    data_source,
    feature_in_tabular_file,
    data_source_analysis,
)
from synesis_api.modules.data_objects.models import feature
from synesis_api.database.service import execute, fetch_all
from synesis_schemas.main_server import TabularFileDataSourceCreate, DataSourceAnalysisCreate, DataSourceCreate


async def create_data_source(
        user_id: uuid.UUID,
        data_source_create: DataSourceCreate,
) -> DataSourceInDB:

    data_source_record = DataSourceInDB(
        id=uuid.uuid4(),
        user_id=user_id,
        **data_source_create.model_dump(),
        created_at=datetime.now()
    )

    await execute(
        insert(data_source).values(data_source_record.model_dump()),
        commit_after=True
    )

    return data_source_record


async def create_data_source_details(
    data_source_details: Union[TabularFileDataSourceCreate],
    # TODO: deal with features
) -> Union[TabularFileDataSourceInDB]:

    if isinstance(data_source_details, TabularFileDataSourceCreate):
        tabular_data_source_record = TabularFileDataSourceInDB(
            id=data_source_details.data_source_id,
            **data_source_details.model_dump(),
            created_at=datetime.now(timezone.utc),
            updated_at=datetime.now(timezone.utc)
        )

        await execute(
            insert(tabular_file_data_source).values(
                tabular_data_source_record.model_dump()),
            commit_after=True
        )

        return tabular_data_source_record


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


async def get_user_data_sources(user_id: uuid.UUID, data_source_ids: Optional[List[uuid.UUID]] = None,) -> List[DataSource]:
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

    feature_in_tabular_file_query = select(feature_in_tabular_file).where(
        feature_in_tabular_file.c.tabular_file_id.in_(source_ids)
    )
    feature_in_tabular_file_records = await fetch_all(feature_in_tabular_file_query)

    feature_query = select(feature).where(
        feature.c.name.in_([record["feature_name"]
                           for record in feature_in_tabular_file_records])
    )
    feature_records = await fetch_all(feature_query)

    # Analysis record

    analysis_query = select(data_source_analysis).where(
        data_source_analysis.c.id.in_(source_ids)
    )
    analysis_records = await fetch_all(analysis_query)

    output_records = []
    for source_id in source_ids:
        source_record = [
            record for record in source_records if record["id"] == source_id][0]

        tabular_record = next(
            [record for record in tabular_source_records if record["id"] == source_id], None)

        if tabular_record:
            feature_names = [record["feature_name"]
                             for record in feature_in_tabular_file_records if record["tabular_file_id"] == source_id]

            type_fields = TabularFileDataSource(
                **tabular_record.model_dump(),
                features=[FeatureInDB(
                    **record) for record in feature_records if record["name"] in feature_names]
            )
        else:
            raise ValueError(
                f"Currently only tabular file data sources are supported, no record found for source ID: {source_id}")

        analysis_record = next(
            [record for record in analysis_records if record["id"] == source_id], None)

        description = get_data_source_description(
            source_record, type_fields, analysis_record)

        output_records.append(DataSource(
            **source_record,
            type_fields=type_fields,
            analysis=analysis_record,
            description_for_agent=description
        ))

    return output_records
