from uuid import UUID
from sqlalchemy import select
from .models import time_series_dataset
from .schema import TimeSeriesDataset
from ..database.service import fetch_one


async def get_time_series_dataset(id: UUID, id_type: str = "dataset_id") -> TimeSeriesDataset:

    if id_type == "dataset_id":
        dataset = await fetch_one(
            select(time_series_dataset).where(time_series_dataset.c.id == id),
            commit_after=True
        )
    elif id_type == "job_id":
        dataset = await fetch_one(
            select(time_series_dataset).where(
                time_series_dataset.c.job_id == id),
            commit_after=True)
    else:
        raise ValueError("Invalid id type")

    return TimeSeriesDataset(**dataset)
