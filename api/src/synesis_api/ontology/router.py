from typing import Annotated, List
from fastapi import APIRouter, Depends
from .service import (
    get_user_time_series_datasets
)
from .schema import TimeSeriesDataset
from ..auth.schema import User
from ..auth.service import get_current_user


router = APIRouter()


@router.get("/time_series_datasets", response_model=List[TimeSeriesDataset])
async def get_time_series_datasets(
    user: Annotated[User, Depends(get_current_user)] = None
) -> List[TimeSeriesDataset]:
    return await get_user_time_series_datasets(user.id)
