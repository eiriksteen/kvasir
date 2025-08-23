import json
from uuid import UUID
from typing import Annotated, List, Optional
from datetime import datetime
from fastapi import APIRouter, Depends, HTTPException, Form, UploadFile

from synesis_api.modules.data_objects.service.metadata_service import (
    create_dataset,
    get_user_datasets,
    get_object_groups
)
from synesis_api.modules.data_objects.service.raw_data_service import get_time_series_payload_data_by_id
from synesis_api.modules.data_objects.schema import (
    DatasetCreate,
    DatasetWithObjectGroups,
    DatasetInDB,
    ObjectGroupsWithListsInDataset,
    TimeSeriesFullWithRawData
)
from synesis_api.auth.schema import User
from synesis_api.auth.service import get_current_user, user_owns_dataset, get_user_from_api_key, user_owns_time_series


router = APIRouter()


@router.post("/dataset")
async def submit_dataset(
    files: list[UploadFile],
    metadata: str = Form(...),
    user: Annotated[User, Depends(get_user_from_api_key)] = None
) -> DatasetInDB:

    metadata_parsed = DatasetCreate(**json.loads(metadata))

    try:
        dataset_record = await create_dataset(files, metadata_parsed, user.id)
    except Exception as e:
        raise HTTPException(
            status_code=400, detail=f"Invalid dataset: {e}")

    return dataset_record


@router.get("/datasets", response_model=List[DatasetWithObjectGroups])
async def fetch_datasets(
    user: Annotated[User, Depends(get_current_user)] = None
) -> List[DatasetWithObjectGroups]:
    """Get all datasets for the current user"""
    return await get_user_datasets(
        user.id,
    )


@router.get("/object-groups-in-dataset/{dataset_id}", response_model=ObjectGroupsWithListsInDataset)
async def fetch_object_groups_in_dataset(
    dataset_id: UUID,
    user: Annotated[User, Depends(get_current_user)] = None
) -> ObjectGroupsWithListsInDataset:
    """Get a specific object group by ID"""

    if not await user_owns_dataset(user.id, dataset_id):
        raise HTTPException(
            status_code=403, detail="Not authorized to access this dataset")

    return await get_object_groups(dataset_id)


@router.get("/time-series-data/{time_series_id}")
async def fetch_time_series_data(
    time_series_id: UUID,
    start_date: Optional[datetime] = None,
    end_date: Optional[datetime] = None,
    user: Annotated[User, Depends(get_current_user)] = None
) -> TimeSeriesFullWithRawData:

    if not await user_owns_time_series(user.id, time_series_id):
        raise HTTPException(
            status_code=403, detail="User does not own dataset")

    time_series = await get_time_series_payload_data_by_id(user.id, time_series_id, start_date, end_date)

    if not time_series:
        raise HTTPException(status_code=404, detail="Time series not found")

    return time_series
