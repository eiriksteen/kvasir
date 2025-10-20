from typing import Annotated, Optional
from fastapi import APIRouter, Depends
from uuid import UUID
from datetime import datetime

from project_server.entity_manager import LocalDatasetManager
from project_server.auth import TokenData, decode_token

from synesis_data_interface.structures.time_series.schema import TimeSeries


router = APIRouter()


@router.get("/time-series-data/{time_series_id}", response_model=TimeSeries)
async def get_time_series_data(
    time_series_id: UUID,
    start_date: Optional[datetime] = None,
    end_date: datetime = datetime.now(),
    token_data: Annotated[TokenData, Depends(decode_token)] = None
) -> TimeSeries:

    dataset_manager = LocalDatasetManager(token_data.bearer_token)
    time_series = await dataset_manager.get_time_series_data_object_with_raw_data(time_series_id, start_date, end_date)
    return time_series
