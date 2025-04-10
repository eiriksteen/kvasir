import uuid
from typing import Annotated, List
from fastapi import APIRouter, Depends
from synesis_api.modules.ontology.service import (
    get_user_time_series_datasets,
    get_user_time_series_dataset_by_id,
    get_user_datasets,
    get_time_series_in_dataset
)
from synesis_api.modules.ontology.schema import TimeSeriesDataset, Datasets, TimeSeries
from synesis_api.auth.schema import User
from synesis_api.auth.service import get_current_user


router = APIRouter()


@router.get("/time-series-datasets", response_model=List[TimeSeriesDataset])
async def get_time_series_datasets(
    user: Annotated[User, Depends(get_current_user)] = None
) -> List[TimeSeriesDataset]:
    return await get_user_time_series_datasets(user.id)

@router.get("/time-series-dataset/{dataset_id}", response_model=TimeSeriesDataset)
async def get_time_series_dataset(
    dataset_id: uuid.UUID,
    user: Annotated[User, Depends(get_current_user)] = None
) -> TimeSeriesDataset:
    return await get_user_time_series_dataset_by_id(dataset_id, user.id)


@router.get("/datasets", response_model=Datasets)
async def get_datasets(
    only_completed: bool = True,
    user: Annotated[User, Depends(get_current_user)] = None
) -> Datasets:
    return await get_user_datasets(user.id, only_completed)


@router.get("/time-series/{dataset_id}", response_model=List[TimeSeries])
async def get_time_series(dataset_id: uuid.UUID) -> List[TimeSeries]:
    return await get_time_series_in_dataset(dataset_id)
