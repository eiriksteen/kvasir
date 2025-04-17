from uuid import UUID
from datetime import datetime
from typing import Annotated, List
from fastapi import APIRouter, Depends
from .service import (
    get_time_series_data
)
from .schema import TimeSeriesData
from ...auth.schema import User
from ...auth.service import get_current_user


router = APIRouter()


@router.get("/time-series/{time_series_id}", response_model=TimeSeriesData)
async def get_time_series(
    time_series_id: UUID,
    start_timestamp: datetime = None,
    end_timestamp: datetime = datetime.now(),
    n_past_values: int = 1024,
) -> TimeSeriesData:
    return await get_time_series_data(
        time_series_id,
        start_timestamp,
        end_timestamp,
        n_past_values
    )
