import json
from uuid import UUID
from typing import Annotated, List, Union
from fastapi import APIRouter, Depends, HTTPException, Form, UploadFile

from synesis_api.modules.data_objects.service import (
    get_object_groups,
    create_dataset,
    get_user_datasets,
    get_data_objects,
    create_object_group,
    create_data_objects,
    update_object_group_raw_data_script_path
)
# from synesis_api.modules.data_objects.service import get_time_series_payload_data_by_id
from synesis_schemas.main_server import (
    DatasetCreate,
    Dataset,
    GetDatasetsByIDsRequest,
    ObjectGroup,
    ObjectGroupWithObjects,
    DataObject,
    ObjectsFile,
    DataObjectGroupCreate,
)
from synesis_schemas.main_server import User
from synesis_api.auth.service import get_current_user, user_owns_dataset, user_owns_object_group, user_owns_data_object


router = APIRouter()


@router.post("/dataset")
async def post_dataset(
    files: list[UploadFile] = [],
    metadata: str = Form(...),
    user: Annotated[User, Depends(get_current_user)] = None
) -> Dataset:
    """Create a new dataset with groups and objects"""

    try:
        dataset_create = DatasetCreate(**json.loads(metadata))
    except Exception as e:
        raise HTTPException(
            status_code=400, detail=f"Invalid metadata: {e}")

    return await create_dataset(user.id, dataset_create, files)


@router.post("/object-group/{dataset_id}", response_model=ObjectGroup)
async def post_object_group(
    dataset_id: UUID,
    group_create: DataObjectGroupCreate,
    files: list[UploadFile] = [],
    user: Annotated[User, Depends(get_current_user)] = None
) -> ObjectGroup:
    """Create an object group in a dataset"""

    if not await user_owns_dataset(user.id, dataset_id):
        raise HTTPException(
            status_code=403, detail="Not authorized to access this dataset")

    return await create_object_group(user.id, dataset_id, group_create, files)


@router.post("/objects/{group_id}")
async def post_objects(
    group_id: UUID,
    files: list[UploadFile] = [],
    metadata: str = Form(...),
    user: Annotated[User, Depends(get_current_user)] = None
) -> List[DataObject]:
    """Create objects in a group (using DataFrame insertion)"""

    if not await user_owns_object_group(user.id, group_id):
        raise HTTPException(
            status_code=403, detail="Not authorized to access this object group")

    try:
        data_list = json.loads(metadata)
        objects_files = [ObjectsFile(**data) for data in data_list]
    except Exception as e:
        raise HTTPException(
            status_code=400, detail=f"Invalid metadata: {e}")

    return await create_data_objects(group_id, files, objects_files)


@router.get("/dataset/{dataset_id}", response_model=Dataset)
async def fetch_dataset(
    dataset_id: UUID,
    user: Annotated[User, Depends(get_current_user)] = None
) -> Dataset:
    """Get a specific dataset by ID"""
    dataset_objs = await get_user_datasets(user.id, dataset_ids=[dataset_id])
    if not dataset_objs:
        raise HTTPException(
            status_code=404, detail="Dataset not found")
    return dataset_objs[0]


@router.get("/datasets-by-ids", response_model=List[Dataset])
async def fetch_datasets_by_ids(
    request: GetDatasetsByIDsRequest,
    user: Annotated[User, Depends(get_current_user)] = None
) -> List[Dataset]:
    """Get a specific dataset by ID"""
    return await get_user_datasets(user.id, dataset_ids=request.dataset_ids)


@router.get("/object-group/{group_id}", response_model=Union[ObjectGroup, ObjectGroupWithObjects])
async def fetch_object_group(
    group_id: UUID,
    include_objects: bool = False,
    user: Annotated[User, Depends(get_current_user)] = None
) -> Union[ObjectGroup, ObjectGroupWithObjects]:
    """Get a specific object group by ID"""

    if not await user_owns_object_group(user.id, group_id):
        raise HTTPException(
            status_code=403, detail="Not authorized to access this object group")

    object_groups = await get_object_groups(group_ids=[group_id], include_objects=include_objects)
    if not object_groups:
        raise HTTPException(
            status_code=404, detail="Object group not found")
    return object_groups[0]


@router.get("/object-groups-in-dataset/{dataset_id}", response_model=List[ObjectGroupWithObjects])
async def fetch_object_groups_in_dataset(
    dataset_id: UUID,
    user: Annotated[User, Depends(get_current_user)] = None
) -> List[ObjectGroupWithObjects]:
    """Get a specific object group by ID"""

    if not await user_owns_dataset(user.id, dataset_id):
        raise HTTPException(
            status_code=403, detail="Not authorized to access this dataset")

    return await get_object_groups(dataset_id=dataset_id, include_objects=True)


@router.get("/data-object/{object_id}", response_model=DataObject)
async def fetch_data_object(
    object_id: UUID,
    user: Annotated[User, Depends(get_current_user)] = None
) -> DataObject:
    """Get a data object"""

    if not await user_owns_data_object(user.id, object_id):
        raise HTTPException(
            status_code=403, detail="Not authorized to access this data object")

    data_objects = await get_data_objects(object_ids=[object_id])
    if not data_objects:
        raise HTTPException(
            status_code=404, detail="Data object not found")
    return data_objects[0]


@router.patch("/object-group/{group_id}/raw-data-script-path", response_model=ObjectGroup)
async def patch_object_group_raw_data_script_path(
    group_id: UUID,
    raw_data_read_script_path: str,
    user: Annotated[User, Depends(get_current_user)] = None
) -> ObjectGroup:
    """Update the raw data read script path for an object group"""

    if not await user_owns_object_group(user.id, group_id):
        raise HTTPException(
            status_code=403, detail="Not authorized to access this object group")

    return await update_object_group_raw_data_script_path(group_id, raw_data_read_script_path)
