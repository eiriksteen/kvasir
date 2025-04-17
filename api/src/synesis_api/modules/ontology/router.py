from uuid import UUID
from typing import Annotated, List
from fastapi import APIRouter, Depends
from .service import (
    get_user_time_series_datasets,
    get_user_datasets,
    get_time_series_in_dataset
)
from .schema import TimeSeriesDataset, Datasets, TimeSeries
from ...auth.schema import User
from ...auth.service import get_current_user


router = APIRouter()


@router.get("/time-series-datasets", response_model=List[TimeSeriesDataset])
async def get_time_series_datasets(
    user: Annotated[User, Depends(get_current_user)] = None
) -> List[TimeSeriesDataset]:
    return await get_user_time_series_datasets(user.id)


@router.get("/datasets", response_model=Datasets)
async def get_datasets(
    user: Annotated[User, Depends(get_current_user)] = None
) -> Datasets:
    return await get_user_datasets(user.id)


@router.get("/time-series/{dataset_id}", response_model=List[TimeSeries])
async def get_time_series(dataset_id: UUID) -> List[TimeSeries]:
    return await get_time_series_in_dataset(dataset_id)
