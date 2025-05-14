from uuid import UUID
from typing import Annotated, List
from fastapi import APIRouter, Depends
from synesis_api.modules.ontology.service import (
    get_user_time_series_datasets,
    get_user_datasets,
    get_time_series_in_dataset
)
from synesis_api.modules.ontology.schema import TimeSeriesInheritedDataset, Datasets, TimeSeries
from synesis_api.auth.schema import User
from synesis_api.auth.service import get_current_user


router = APIRouter()


@router.get("/time-series-datasets", response_model=List[TimeSeriesInheritedDataset])
async def get_time_series_datasets(
    user: Annotated[User, Depends(get_current_user)] = None
) -> List[TimeSeriesInheritedDataset]:
    return await get_user_time_series_datasets(user.id)


@router.get("/datasets", response_model=Datasets)
async def get_datasets(
    only_completed: bool = True,
    user: Annotated[User, Depends(get_current_user)] = None
) -> Datasets:
    return await get_user_datasets(user.id, only_completed)


@router.get("/time-series/{dataset_id}", response_model=List[TimeSeries])
async def get_time_series(dataset_id: UUID) -> List[TimeSeries]:
    return await get_time_series_in_dataset(dataset_id)
