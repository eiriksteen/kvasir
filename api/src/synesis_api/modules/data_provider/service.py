import pandas as pd
from datetime import datetime, timezone
from uuid import UUID
from pathlib import Path
from fastapi import HTTPException
from typing import List
from synesis_api.modules.data_provider.schema import TimeSeriesData, EntityMetadata, TimeSeriesDataWithMetadata
from synesis_api.modules.data_provider.sources.local import fetch_entity_metadata_local, fetch_time_series_data_local, fetch_metadata_all_local


async def get_time_series_data(
    user_id: UUID,
    time_series_id: UUID,
    start_timestamp: datetime | None = None,
    end_timestamp: datetime = datetime.now(timezone.utc),
    include_metadata: bool = False
) -> TimeSeriesData:

    # source = get_source(time_series_id)
    source = "local"

    if source == "local":
        return await fetch_time_series_data_local(user_id, time_series_id, start_timestamp, end_timestamp, include_metadata=include_metadata)
    else:
        raise HTTPException(
            status_code=400, detail="Invalid source, currently only local source is supported")


async def get_entity_metadata(
    entity_id: UUID,
    user_id: UUID
) -> EntityMetadata:

    # source = get_source(entity_id)
    source = "local"

    if source == "local":
        return await fetch_entity_metadata_local(user_id, entity_id)
    else:
        raise HTTPException(
            status_code=400, detail="Invalid source, currently only local source is supported")


async def get_all_entity_metadata(
    user_id: UUID,
    dataset_id: UUID
) -> List[EntityMetadata]:

    # source = get_source(dataset_id)
    source = "local"

    if source == "local":
        return await fetch_metadata_all_local(user_id, dataset_id)
    else:
        raise HTTPException(
            status_code=400, detail="Invalid source, currently only local source is supported")
