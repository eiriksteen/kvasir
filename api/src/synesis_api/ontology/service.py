from uuid import UUID
from typing import List
from sqlalchemy import select
from .models import time_series_dataset
from .schema import TimeSeriesDataset
from ..database.service import fetch_all


async def get_user_time_series_datasets(user_id: UUID) -> List[TimeSeriesDataset]:
    datasets = await fetch_all(
        select(time_series_dataset).where(
            time_series_dataset.c.user_id == user_id)
    )
    return [TimeSeriesDataset(**dataset) for dataset in datasets]
