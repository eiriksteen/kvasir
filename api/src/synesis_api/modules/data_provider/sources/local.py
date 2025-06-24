import uuid
import pandas as pd
from io import StringIO
from typing import List
from pathlib import Path
from aiofiles import open as aiofiles_open
from synesis_api.modules.ontology.models import time_series, time_series_dataset, dataset_metadata
from synesis_api.database.service import fetch_one, fetch_all
from synesis_api.modules.data_provider.schema import TimeSeriesData, EntityMetadata, TimeSeriesDataWithMetadata
from sqlalchemy import select
from datetime import datetime, timezone


async def fetch_time_series_data_local(
        user_id: uuid.UUID,
        time_series_id: uuid.UUID,
        start_timestamp: datetime | None = None,
        end_timestamp: datetime = datetime.now(timezone.utc),
        n_past_values_default: int = 196,
        include_metadata: bool = False
) -> TimeSeriesData:

    query = select(
        time_series.c.id,
        time_series.c.original_id,
        time_series.c.dataset_id,
        time_series_dataset.c.index_first_level,
        time_series_dataset.c.index_second_level
    ).join(
        time_series_dataset,
        time_series.c.dataset_id == time_series_dataset.c.id
    ).where(
        time_series.c.id == time_series_id
    )

    time_series_data = await fetch_one(query)
    dataset_id = time_series_data["dataset_id"]
    original_id = time_series_data["original_id"]
    index_first_level = time_series_data["index_first_level"]
    index_second_level = time_series_data["index_second_level"]

    data_path = Path("integrated_data") / str(user_id) / \
        str(dataset_id) / "dataset.csv"

    async with aiofiles_open(data_path, mode="r") as f:
        data = await f.read()

    data_df = pd.read_csv(StringIO(data))

    if index_first_level:
        data_df = data_df.set_index(index_first_level)
    if index_second_level:
        # Convert first level index to string
        data_df.index = data_df.index.astype(str)
        data_df = data_df.set_index(index_second_level, append=True)

    time_series_data = data_df.loc[original_id]

    if end_timestamp:
        time_series_data = time_series_data[time_series_data.index <= end_timestamp]
    if start_timestamp:
        time_series_data = time_series_data[time_series_data.index >=
                                            start_timestamp]
    else:
        time_series_data = time_series_data.tail(n_past_values_default)

    # Convert to schema format
    timestamps = time_series_data.index.tolist()
    values = [[None if pd.isna(x) else x for x in row]
              for row in time_series_data.values.transpose().tolist()]
    feature_names = time_series_data.columns.tolist()

    if include_metadata:
        metadata = await fetch_entity_metadata_local(user_id, time_series_id)

        return TimeSeriesDataWithMetadata(
            id=time_series_id,
            original_id=str(original_id),
            timestamps=timestamps,
            values=values,
            feature_names=feature_names,
            metadata=metadata
        )

    return TimeSeriesData(
        id=time_series_id,
        original_id=str(original_id),
        timestamps=timestamps,
        values=values,
        feature_names=feature_names
    )


async def fetch_entity_metadata_local(user_id: uuid.UUID, entity_id: uuid.UUID) -> EntityMetadata:

    query = select(
        time_series.c.original_id,
        time_series.c.dataset_id,
        time_series_dataset.c.index_first_level,
        time_series_dataset.c.index_second_level
    ).join(
        time_series_dataset,
        time_series.c.dataset_id == time_series_dataset.c.id
    ).where(
        time_series.c.id == entity_id
    )
    result = await fetch_one(query)
    original_id = result["original_id"]
    dataset_id = result["dataset_id"]
    index_first_level = result["index_first_level"]
    index_second_level = result["index_second_level"]

    metadata_query = select(
        dataset_metadata.c.column_names,
        dataset_metadata.c.column_types
    ).where(
        dataset_metadata.c.dataset_id == dataset_id
    )
    metadata_result = await fetch_one(metadata_query)
    column_names = metadata_result["column_names"]
    column_types = metadata_result["column_types"]

    metadata_path = Path("integrated_data") / str(user_id) / \
        str(dataset_id) / "metadata.csv"
    async with aiofiles_open(metadata_path, mode="r") as f:
        data = await f.read()

    metadata_df = pd.read_csv(StringIO(data))
    if index_first_level and index_second_level:
        metadata_df = metadata_df.set_index(index_first_level)
        metadata_df.index = metadata_df.index.astype(str)

    else:
        raise ValueError(
            "Both index_first_level and index_second_level must be provided")

    entity_metadata = metadata_df.loc[original_id]
    values = [None if pd.isna(x) else x for x in entity_metadata.tolist()]

    return EntityMetadata(
        dataset_id=dataset_id,
        entity_id=entity_id,
        original_id=original_id,
        original_id_name=index_first_level,
        column_names=column_names,
        column_types=column_types,
        values=values
    )


async def fetch_metadata_all_local(user_id: uuid.UUID, dataset_id: uuid.UUID) -> List[EntityMetadata]:
    metadata_query = select(
        dataset_metadata.c.column_names,
        dataset_metadata.c.column_types,
        time_series_dataset.c.index_first_level
    ).join(
        time_series_dataset,
        dataset_metadata.c.dataset_id == time_series_dataset.c.id
    ).where(
        dataset_metadata.c.dataset_id == dataset_id
    )

    metadata_result = await fetch_one(metadata_query)

    column_names = metadata_result["column_names"]
    column_types = metadata_result["column_types"]
    index_first_level = metadata_result["index_first_level"]

    metadata_path = Path("integrated_data") / str(user_id) / \
        str(dataset_id) / "metadata.csv"
    async with aiofiles_open(metadata_path, mode="r") as f:
        data = await f.read()

    metadata_df = pd.read_csv(StringIO(data))

    query = select(
        time_series.c.id,
        time_series.c.original_id
    ).where(
        time_series.c.dataset_id == dataset_id
    )
    entities = await fetch_all(query)

    id_map = {entity["original_id"]: entity["id"] for entity in entities}

    return [
        EntityMetadata(
            dataset_id=dataset_id,
            original_id_name=index_first_level,
            entity_id=id_map[str(row[index_first_level])],
            original_id=str(row[index_first_level]),
            column_names=column_names,
            column_types=column_types,
            values=[None if pd.isna(row[col]) else row[col]
                    for col in column_names]
        )
        for _, row in metadata_df.iterrows()
    ]
