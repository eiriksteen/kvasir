from uuid import UUID
from typing import List
from sqlalchemy import select, join
from .models import time_series_dataset, dataset
from .schema import TimeSeriesDataset, Datasets
from ...database.service import fetch_all, fetch_one


async def get_user_time_series_datasets(user_id: UUID) -> List[TimeSeriesDataset]:
    query = select(dataset, time_series_dataset).join(
        time_series_dataset, dataset.c.id == time_series_dataset.c.id
    ).where(dataset.c.user_id == user_id)

    datasets = await fetch_all(query)
    return [TimeSeriesDataset(**dataset) for dataset in datasets]


async def get_user_datasets(user_id: UUID) -> Datasets:
    time_series = await get_user_time_series_datasets(user_id)
    return Datasets(time_series=time_series)


async def get_user_datasets_by_ids(user_id: UUID, dataset_ids: List[UUID] = []) -> Datasets:
    time_series_query = select(dataset, time_series_dataset).join(
        time_series_dataset, dataset.c.id == time_series_dataset.c.id
    ).where(
        dataset.c.user_id == user_id,
        dataset.c.id.in_(dataset_ids)
    )

    time_series_datasets = await fetch_all(time_series_query)
    return Datasets(time_series=[TimeSeriesDataset(**dataset) for dataset in time_series_datasets])


async def get_user_time_series_dataset(user_id: UUID, dataset_id: UUID) -> TimeSeriesDataset:
    query = select(dataset, time_series_dataset).join(
        time_series_dataset, dataset.c.id == time_series_dataset.c.id
    ).where(
        dataset.c.user_id == user_id,
        dataset.c.id == dataset_id
    )

    dataset = await fetch_one(query)
    return TimeSeriesDataset(**dataset)
