import uuid
import pandas as pd
from pathlib import Path
from datetime import datetime, timezone
from typing import List, Optional, Tuple
from fastapi import UploadFile
from sqlalchemy import insert, select, update, case
from synesis_api.modules.data_objects.schema import FeatureInDB
from synesis_api.modules.data_sources.schema import (
    TabularFileDataSource,
    DataSourceInDB,
    FileDataSourceInDB,
    TabularFileDataSourceInDB,
    FeatureInTabularFileInDB,
    DataSource,
)
from synesis_api.modules.data_sources.models import (
    file_data_source,
    tabular_file_data_source,
    data_source,
    feature_in_tabular_file,
)
from synesis_api.modules.data_objects.models import feature
from synesis_api.database.service import execute, fetch_all
from synesis_api.storage.local import save_raw_file_to_local_storage
from synesis_api.modules.data_objects.service.metadata_service import create_features


async def _create_data_sources(
        user_id: uuid.UUID,
        types: List[str],
        names: List[str],
        descriptions: List[Optional[str]],
        content_previews: List[Optional[str]]
) -> List[DataSourceInDB]:

    data_source_records: List[DataSourceInDB] = []

    for type, name, description, content_preview in zip(types, names, descriptions, content_previews):
        data_source_id = uuid.uuid4()

        data_source_record = DataSourceInDB(
            id=data_source_id,
            user_id=user_id,
            type=type,
            name=name,
            description=description,
            content_preview=content_preview,
            created_at=datetime.now()
        )
        data_source_records.append(data_source_record)

    data_source_records_dump = [data_source_record.model_dump()
                                for data_source_record in data_source_records]
    await execute(
        insert(data_source).values(data_source_records_dump),
        commit_after=True
    )

    return data_source_records


async def _create_file_data_sources(
    user_id: uuid.UUID,
    descriptions: List[Optional[str]],
    content_previews: List[Optional[str]],
    files: list[UploadFile]
) -> List[FileDataSourceInDB]:

    # Create the base data source record
    data_sources = await _create_data_sources(
        user_id=user_id,
        types=["TabularFile"]*len(files),
        names=[file.filename for file in files],
        descriptions=descriptions,
        content_previews=content_previews
    )

    file_paths: List[Path] = []
    for file, data_source in zip(files, data_sources):
        file_path = await save_raw_file_to_local_storage(
            user_id=user_id,
            file_id=data_source.id,
            file=file
        )
        file_paths.append(file_path)

    # Create the file data source record
    file_records = [FileDataSourceInDB(
        id=data_source.id,
        file_name=file.filename,
        file_path=str(file_path.resolve()),
        file_type=file.content_type,
        file_size_bytes=file.size,
        created_at=datetime.now(timezone.utc),
        updated_at=datetime.now(timezone.utc)
    ) for file_path, data_source in zip(file_paths, data_sources)]

    file_records_dump = [file_record.model_dump()
                         for file_record in file_records]

    await execute(
        insert(file_data_source).values(file_records_dump),
        commit_after=True
    )

    return file_records


async def create_tabular_file_data_sources(
    user_id: uuid.UUID,
    files: list[UploadFile]
) -> Tuple[List[TabularFileDataSourceInDB], List[FileDataSourceInDB]]:

    file_records = await _create_file_data_sources(
        user_id=user_id,
        descriptions=[None for _ in range(len(files))],
        content_previews=[None for _ in range(len(files))],
        files=files
    )

    file_record_ids = [file_record.id for file_record in file_records]

    num_rows_per_file = []
    num_columns_per_file = []

    for file_record in file_records:
        if Path(file_record.file_path).suffix == ".csv":
            df = pd.read_csv(file_record.file_path)
        elif Path(file_record.file_path).suffix == ".xlsx":
            df = pd.read_excel(file_record.file_path)
        elif Path(file_record.file_path).suffix == ".json":
            df = pd.read_json(file_record.file_path)
        elif Path(file_record.file_path).suffix == ".parquet":
            df = pd.read_parquet(file_record.file_path)
        else:
            raise ValueError(
                f"Unsupported file type: {Path(file_record.file_path).suffix}")

        num_rows_per_file.append(len(df))
        num_columns_per_file.append(len(df.columns))

    # We then insert the tabular records
    tabular_records = [TabularFileDataSourceInDB(
        id=file_id,
        num_rows=num_rows,
        num_columns=num_columns,
        created_at=datetime.now(timezone.utc),
        updated_at=datetime.now(timezone.utc)
    ) for file_id, num_rows, num_columns in zip(file_record_ids, num_rows_per_file, num_columns_per_file)]

    tabular_records_dump = [tabular_record.model_dump()
                            for tabular_record in tabular_records]

    await execute(
        insert(tabular_file_data_source).values(tabular_records_dump),
        commit_after=True
    )

    return tabular_records, file_records


async def fill_tabular_file_data_sources_details(
    file_record_ids: Optional[List[uuid.UUID]],
    descriptions: List[str],
    quality_descriptions: List[str],
    content_previews: List[str],
    feature_names: List[List[str]],
    feature_units: List[List[str]],
    feature_descriptions: List[List[str]],
    feature_types: List[List[str]],
    feature_subtypes: List[List[str]],
    feature_scales: List[List[str]]
):

    check_query = select(
        tabular_file_data_source
    ).where(
        tabular_file_data_source.c.id.in_(file_record_ids)
    )
    check_results = await fetch_all(check_query)

    assert len(check_results) == len(
        file_record_ids), "Each file_id must correspond to a tabular file"

    # We need to first update the data_source model with descriptions, quality descriptions, and content previews
    # Create case statements for each column to map file_id to corresponding values
    description_case = case(
        {file_id: desc for file_id, desc in zip(
            file_record_ids, descriptions)},
        value=data_source.c.id
    )
    quality_case = case(
        {file_id: qual for file_id, qual in zip(
            file_record_ids, quality_descriptions)},
        value=data_source.c.id
    )
    content_case = case(
        {file_id: content for file_id, content in zip(
            file_record_ids, content_previews)},
        value=data_source.c.id
    )

    await execute(
        update(data_source)
        .where(data_source.c.id.in_(file_record_ids))
        .values(
            description=description_case,
            quality_description=quality_case,
            content_preview=content_case
        ),
        commit_after=True
    )

    # Finally we insert the features into data object, then assign features to the tabular file

    await create_features(
        # Flatten the lists
        names=[f for l in feature_names for f in l],
        units=[f for l in feature_units for f in l],
        descriptions=[f for l in feature_descriptions for f in l],
        types=[f for l in feature_types for f in l],
        subtypes=[f for l in feature_subtypes for f in l],
        scales=[f for l in feature_scales for f in l]
    )

    # Finally we assign the features to the tabular file
    feature_assignments = [FeatureInTabularFileInDB(
        feature_name=feature_name,
        tabular_file_id=file_id,
        created_at=datetime.now(timezone.utc),
        updated_at=datetime.now(timezone.utc)
    ).model_dump() for file_id, features in zip(file_record_ids, feature_names) for feature_name in features]

    await execute(
        insert(feature_in_tabular_file).values(feature_assignments),
        commit_after=True
    )


async def fetch_data_sources(user_id: uuid.UUID) -> List[DataSource]:
    """Fetch all data sources for a user, returning the most specific type"""

    tabular_file_query = select(
        data_source,
        file_data_source,
        tabular_file_data_source
    ).join(
        file_data_source,
        data_source.c.id == file_data_source.c.id,
    ).join(
        tabular_file_data_source,
        file_data_source.c.id == tabular_file_data_source.c.id,
    ).where(
        data_source.c.user_id == user_id
    )

    tabular_file_sources = await fetch_all(tabular_file_query)

    features_in_source_query = select(
        feature,
        feature_in_tabular_file.c.tabular_file_id
    ).join(
        feature_in_tabular_file,
        feature.c.name == feature_in_tabular_file.c.feature_name
    )

    features_in_source = await fetch_all(features_in_source_query)

    tabular_file_sources_objects = [TabularFileDataSource(
        **source,
        # Get the features corresponding to this source id
        features=[FeatureInDB(
            **f) for f in features_in_source if f["tabular_file_id"] == source["id"]]
    ) for source in tabular_file_sources]

    # TODO: More sources coming up

    return tabular_file_sources_objects


async def get_data_sources_by_ids(data_source_ids: List[uuid.UUID]) -> List[DataSource]:
    """Get a data source by ID, returning the most specific type"""
    # Get the base data source

    tabular_records_query = select(
        data_source,
        file_data_source,
        tabular_file_data_source
    ).join(
        file_data_source,
        data_source.c.id == file_data_source.c.id,
    ).join(
        tabular_file_data_source,
        file_data_source.c.id == tabular_file_data_source.c.id,
    ).where(
        data_source.c.id.in_(data_source_ids)
    )

    tabular_records = await fetch_all(tabular_records_query)

    features_in_source_query = select(
        feature
    ).join(
        feature_in_tabular_file,
        feature.c.name == feature_in_tabular_file.c.feature_name
    )

    features_in_source = await fetch_all(features_in_source_query)

    tabular_objects = [TabularFileDataSource(
        **tabular_record,
        features=[FeatureInDB(**feature) for feature in features_in_source]
    ) for tabular_record in tabular_records]

    return tabular_objects
