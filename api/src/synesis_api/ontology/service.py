from uuid import UUID
from typing import List
from sqlalchemy import select
from .models import time_series_dataset
from .schema import TimeSeriesDataset, Datasets
from ..database.service import fetch_all
from .schema import TimeSeriesDataset
from ..database.service import fetch_all, fetch_one


async def get_user_time_series_datasets(user_id: UUID) -> List[TimeSeriesDataset]:
    datasets = await fetch_all(
        select(time_series_dataset).where(
            time_series_dataset.c.user_id == user_id)
    )
    return [TimeSeriesDataset(**dataset) for dataset in datasets]


async def get_user_datasets(user_id: UUID) -> Datasets:
    return Datasets(
        time_series=await get_user_time_series_datasets(user_id),
        num_datasets=0
    )


async def get_user_time_series_dataset(user_id: UUID, dataset_id: UUID) -> TimeSeriesDataset:
    dataset = await fetch_one(
        select(time_series_dataset).where(
            time_series_dataset.c.user_id == user_id, time_series_dataset.c.id == dataset_id)
    )
    return TimeSeriesDataset(**dataset)
