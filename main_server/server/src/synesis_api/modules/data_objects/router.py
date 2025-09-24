import json
from uuid import UUID
from typing import Annotated, List, Optional, Union
from datetime import datetime
from fastapi import APIRouter, Depends, HTTPException, Form, UploadFile

from synesis_api.modules.data_objects.service import (
    get_object_groups_in_dataset_with_entities_and_features,
    get_user_dataset_by_id,
    get_object_group,
    create_dataset,
    get_project_datasets,
    get_user_datasets_by_ids
)
# from synesis_api.modules.data_objects.service import get_time_series_payload_data_by_id
from synesis_schemas.main_server import (
    DatasetCreate,
    DatasetFull,
    DatasetFullWithFeatures,
    TimeSeriesFullWithRawData,
    ObjectGroupInDB,
    ObjectGroupWithFeatures,
    ObjectGroupWithEntitiesAndFeatures,
    GetDatasetByIDsRequest
)
from synesis_schemas.main_server import User
from synesis_api.auth.service import get_current_user, user_owns_dataset, user_owns_object_group


router = APIRouter()


@router.post("/dataset")
async def submit_dataset(
    files: list[UploadFile],
    metadata: str = Form(...),
    user: Annotated[User, Depends(get_current_user)] = None
) -> DatasetFull:

    try:
        metadata_parsed = DatasetCreate(**json.loads(metadata))
    except Exception as e:
        raise HTTPException(
            status_code=400, detail=f"Invalid metadata: {e}")

    dataset_record = await create_dataset(files, metadata_parsed, user.id)

    return dataset_record


@router.get("/project-datasets/{project_id}", response_model=List[Union[DatasetFullWithFeatures, DatasetFull]])
async def fetch_datasets(
    project_id: UUID,
    include_features: bool = False,
    user: Annotated[User, Depends(get_current_user)] = None
) -> List[Union[DatasetFullWithFeatures, DatasetFull]]:
    """Get all datasets for the current user"""
    return await get_project_datasets(user.id, project_id, include_features=include_features)


@router.get("/dataset/{dataset_id}", response_model=Union[DatasetFullWithFeatures, DatasetFull])
async def fetch_dataset(
    dataset_id: UUID,
    include_features: bool = False,
    user: Annotated[User, Depends(get_current_user)] = None
) -> Union[DatasetFullWithFeatures, DatasetFull]:
    """Get a specific dataset by ID"""
    return await get_user_dataset_by_id(dataset_id, user.id, include_features=include_features)


@router.get("/datasets-by-ids", response_model=List[Union[DatasetFullWithFeatures, DatasetFull]])
async def fetch_datasets_by_ids(
    request: GetDatasetByIDsRequest,
    user: Annotated[User, Depends(get_current_user)] = None
) -> List[Union[DatasetFullWithFeatures, DatasetFull]]:
    """Get a specific dataset by ID"""
    return await get_user_datasets_by_ids(user.id, dataset_ids=request.dataset_ids, include_features=request.include_features, max_features=50)


@router.get("/object-group/{group_id}", response_model=Union[ObjectGroupInDB, ObjectGroupWithFeatures, ObjectGroupWithEntitiesAndFeatures])
async def fetch_object_group(
    group_id: UUID,
    include_features: bool = False,
    include_entities: bool = False,
    user: Annotated[User, Depends(get_current_user)] = None
) -> Union[ObjectGroupInDB, ObjectGroupWithFeatures, ObjectGroupWithEntitiesAndFeatures]:
    """Get a specific object group by ID"""

    if not await user_owns_object_group(user.id, group_id):
        raise HTTPException(
            status_code=403, detail="Not authorized to access this object group")

    return await get_object_group(group_id, include_features=include_features, include_entities=include_entities)


@router.get("/object-groups-in-dataset/{dataset_id}", response_model=List[ObjectGroupWithEntitiesAndFeatures])
async def fetch_object_groups_in_dataset(
    dataset_id: UUID,
    user: Annotated[User, Depends(get_current_user)] = None
) -> List[ObjectGroupWithEntitiesAndFeatures]:
    """Get a specific object group by ID"""

    if not await user_owns_dataset(user.id, dataset_id):
        raise HTTPException(
            status_code=403, detail="Not authorized to access this dataset")

    return await get_object_groups_in_dataset_with_entities_and_features(dataset_id)


@router.get("/time-series-data/{time_series_id}")
async def fetch_time_series_data(
    time_series_id: UUID,
    start_date: Optional[datetime] = None,
    end_date: Optional[datetime] = None,
    user: Annotated[User, Depends(get_current_user)] = None
) -> TimeSeriesFullWithRawData:

    raise HTTPException(status_code=501, detail="Not implemented")

    # if not await user_owns_time_series(user.id, time_series_id):
    #     raise HTTPException(
    #         status_code=403, detail="User does not own dataset")

    # time_series = await get_time_series_payload_data_by_id(user.id, time_series_id, start_date, end_date)

    # if not time_series:
    #     raise HTTPException(status_code=404, detail="Time series not found")

    # return time_series
