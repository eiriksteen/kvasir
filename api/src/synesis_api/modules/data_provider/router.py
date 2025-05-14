from uuid import UUID
from datetime import datetime
from typing import Annotated, List, Union
from fastapi import APIRouter, Depends, HTTPException
from synesis_api.modules.data_provider.service import (
    get_all_entity_metadata,
    get_time_series_data,
    get_entity_metadata
)
from synesis_api.modules.data_provider.schema import EntityMetadata, TimeSeriesDataWithMetadata, TimeSeriesData
from synesis_api.auth.schema import User
from synesis_api.auth.service import get_current_user, user_owns_dataset, user_owns_data_entity


router = APIRouter()


@router.get("/all-metadata/{dataset_id}", response_model=List[EntityMetadata])
async def get_all_entity_metadata_route(
    dataset_id: UUID,
    current_user: Annotated[User, Depends(get_current_user)]
) -> List[EntityMetadata]:

    if not await user_owns_dataset(current_user.id, dataset_id):
        raise HTTPException(
            status_code=403, detail="You do not have permission to access this dataset")

    metadata = await get_all_entity_metadata(current_user.id, dataset_id)

    return metadata


@router.get("/time-series/{time_series_id}", response_model=Union[TimeSeriesDataWithMetadata, TimeSeriesData])
async def get_time_series_with_metadata_route(
    time_series_id: UUID,
    current_user: Annotated[User, Depends(get_current_user)],
    start_timestamp: datetime | None = None,
    end_timestamp: datetime = None,
    include_metadata: bool = False
) -> TimeSeriesDataWithMetadata:

    if not await user_owns_data_entity(current_user.id, time_series_id):
        raise HTTPException(
            status_code=403, detail="You do not have permission to access this time series")

    data = await get_time_series_data(
        current_user.id,
        time_series_id,
        start_timestamp,
        end_timestamp,
        include_metadata
    )

    return data


@router.get("/metadata/{entity_id}", response_model=EntityMetadata)
async def get_entity_metadata_route(
    entity_id: UUID,
    current_user: Annotated[User, Depends(get_current_user)]
) -> EntityMetadata:
    return await get_entity_metadata(entity_id, current_user.id)
