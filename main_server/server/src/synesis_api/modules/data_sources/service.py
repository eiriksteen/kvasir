import uuid
from datetime import datetime, timezone
from typing import List, Optional, Union
from sqlalchemy import insert, select

from synesis_schemas.main_server import FeatureInDB
from synesis_schemas.main_server import (
    DataSourceInDB,
    TabularFileDataSourceInDB,
    # FeatureInTabularFileInDB,
    DataSourceAnalysisInDB,
    DataSource,
    TabularFileDataSource,
    DetailedDataSourceRecords,
)
from synesis_api.modules.data_sources.models import (
    tabular_file_data_source,
    data_source,
    feature_in_tabular_file,
    data_source_analysis,
)
from synesis_api.modules.data_objects.models import feature
from synesis_api.database.service import execute, fetch_all
from synesis_api.modules.project.service import get_data_source_ids_in_project
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
    # features: Optional[List[FeatureInDB]] = None
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
    # else:
    #     raise ValueError(
    #         f"Unsupported data source details type: {type(data_source_details)}")


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


async def get_data_sources(
    data_source_ids: Optional[List[uuid.UUID]] = None,
    user_id: Optional[uuid.UUID] = None,
) -> List[DataSource]:
    """Get a data source by ID, returning the most specific type"""
    # Get the base data source

    assert user_id is not None or (data_source_ids is not None and not len(
        data_source_ids) == 0), "Either user_id or data_source_ids must be provided"

    data_source_query = select(data_source)

    if user_id:
        data_source_query = data_source_query.where(
            data_source.c.user_id == user_id
        )
    if data_source_ids and len(data_source_ids) > 0:
        data_source_query = data_source_query.where(
            data_source.c.id.in_(data_source_ids)
        )

    source_records = await fetch_all(data_source_query)
    detailed_records = await _get_detailed_records([record["id"] for record in source_records])

    output_records = []
    for source_id in [record["id"] for record in source_records]:
        source_record = [
            record for record in source_records if record["id"] == source_id][0]

        tabular_records = [
            record for record in detailed_records.tabular_records if record.id == source_id]

        if tabular_records:
            output_records.append(tabular_records[0])
        # elif s3_record: ...
        else:
            output_records.append(DataSourceInDB(**source_record))

    return output_records


async def get_project_data_sources(
    user_id: uuid.UUID,
    project_id: uuid.UUID,
) -> List[DataSource]:
    data_sources_ids_in_project = await get_data_source_ids_in_project(project_id)
    return await get_data_sources(user_id=user_id, data_source_ids=data_sources_ids_in_project)


# Add other data source types here
async def _get_detailed_records(data_source_ids: List[uuid.UUID]) -> DetailedDataSourceRecords:

    tabular_records_query = select(
        data_source,
        tabular_file_data_source
    ).join(
        tabular_file_data_source,
        data_source.c.id == tabular_file_data_source.c.id,
    ).where(
        data_source.c.id.in_(data_source_ids),
        data_source.c.type == "file"
    )

    tabular_records = await fetch_all(tabular_records_query)

    features_in_source_query = select(
        feature
    ).join(
        feature_in_tabular_file,
        feature.c.name == feature_in_tabular_file.c.feature_name
    )

    features_in_source = await fetch_all(features_in_source_query)

    analysis_query = select(
        data_source_analysis
    ).where(
        data_source_analysis.c.data_source_id.in_(data_source_ids)
    )
    analysis_result = await fetch_all(analysis_query)

    tabular_records_detailed = []
    for tabular_rec_in_db in tabular_records:
        analysis_records = [
            record for record in analysis_result if record["data_source_id"] == tabular_rec_in_db["id"]]
        features_in_source_records = [
            record for record in features_in_source if record["tabular_file_id"] == tabular_rec_in_db["id"]]
        tabular_records_detailed.append(TabularFileDataSource(
            **tabular_rec_in_db,
            features=[FeatureInDB(**feature)
                      for feature in features_in_source_records],
            analysis=DataSourceAnalysisInDB(**analysis_records[0]) if analysis_records else None))

    return DetailedDataSourceRecords(
        tabular_records=tabular_records_detailed
    )
