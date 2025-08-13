from uuid import UUID
from typing import Optional
from datetime import datetime
from sqlalchemy import select
from fastapi import HTTPException

from synesis_api.database.service import fetch_one
from synesis_api.storage.local import read_dataframe_from_local_storage
from synesis_api.modules.data_objects.models import (
    dataset,
    time_series,
    object_group,
    data_object,
)
from synesis_api.secrets import DEFAULT_TIME_SERIES_PAYLOAD_LEN
from synesis_api.modules.data_objects.schema import TimeSeriesFullWithRawData
from synesis_api.modules.data_objects.service.metadata_service import feature_metadata_to_df
from synesis_api.utils import timezone_str_to_tz_info


from synesis_data_structures.time_series.serialization import serialize_dataframes_to_api_payloads
from synesis_data_structures.time_series.definitions import (
    TIME_SERIES_DATA_SECOND_LEVEL_ID,
    FEATURE_INFORMATION_SECOND_LEVEL_ID,
)


# This can import from metadata_service, but not the other way around


# Functions to:
# - get raw data (combined with metadata) payload to send it to the client
# - combine stored raw parquet with metadata to prepare parquet files to be sent to processing units


# TODO: This is inefficient, shouldn't load the whole dataframe
async def get_time_series_payload_data_by_id(
    user_id: UUID,
    time_series_id: UUID,
    start_date: Optional[datetime] = None,
    end_date: Optional[datetime] = None
) -> TimeSeriesFullWithRawData:

    ts_metadata = await fetch_one(
        select(
            data_object.c.name,
            data_object.c.description,
            data_object.c.additional_variables,
            data_object.c.original_id,
            data_object.c.created_at,
            data_object.c.updated_at,
            time_series.c.num_timestamps,
            time_series.c.start_timestamp,
            time_series.c.end_timestamp,
            time_series.c.sampling_frequency,
            time_series.c.timezone,
            object_group.c.id.label("group_id"),
            dataset.c.id.label("dataset_id")
        ).join(
            time_series,
            data_object.c.id == time_series.c.id
        ).join(
            object_group,
            data_object.c.group_id == object_group.c.id
        ).join(
            dataset,
            object_group.c.dataset_id == dataset.c.id
        ).where(
            data_object.c.id == time_series_id
        )
    )

    if not ts_metadata:
        raise HTTPException(status_code=404, detail="Time series not found")

    dataframe = read_dataframe_from_local_storage(
        user_id,
        ts_metadata["dataset_id"],
        ts_metadata["group_id"],
        "time_series_data"
    )

    if not end_date:
        end_date = ts_metadata["end_timestamp"]
    if not start_date:
        start_date = dataframe.loc[ts_metadata["original_id"]].index.tolist()[
            -DEFAULT_TIME_SERIES_PAYLOAD_LEN]

    start_date = start_date.replace(
        tzinfo=timezone_str_to_tz_info(ts_metadata["timezone"]))
    end_date = end_date.replace(
        tzinfo=timezone_str_to_tz_info(ts_metadata["timezone"]))

    dataframe.index = dataframe.index.map(lambda x: (x[0], x[1].replace(
        tzinfo=timezone_str_to_tz_info(ts_metadata["timezone"]))))

    series = dataframe.loc[(ts_metadata["original_id"], start_date):(
        ts_metadata["original_id"], end_date)]

    feature_metadata_df = await feature_metadata_to_df(group_id=ts_metadata["group_id"])

    data_serialized = serialize_dataframes_to_api_payloads(
        {TIME_SERIES_DATA_SECOND_LEVEL_ID: series,
         FEATURE_INFORMATION_SECOND_LEVEL_ID: feature_metadata_df},
        "time_series")[0]

    payload = TimeSeriesFullWithRawData(
        **data_serialized.model_dump(),
        name=ts_metadata["name"],
        description=ts_metadata["description"],
        original_id=ts_metadata["original_id"],
        group_id=ts_metadata["group_id"],
        num_timestamps=ts_metadata["num_timestamps"],
        start_timestamp=ts_metadata["start_timestamp"],
        end_timestamp=ts_metadata["end_timestamp"],
        sampling_frequency=ts_metadata["sampling_frequency"],
        timezone=ts_metadata["timezone"],
        created_at=ts_metadata["created_at"],
        updated_at=ts_metadata["updated_at"]
    )

    payload.additional_variables = ts_metadata["additional_variables"]

    return payload
