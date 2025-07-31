import json
from uuid import UUID
from typing import Annotated, List, Union
from fastapi import APIRouter, Depends, HTTPException, Form, UploadFile
from synesis_api.modules.data_objects.service import (
    create_dataset,
    get_user_dataset,
    get_user_datasets,
    get_user_datasets_by_ids
)
from synesis_api.modules.data_objects.schema import (
    DatasetCreate,
    DatasetWithObjectGroups,
    DatasetWithObjectGroupsAndLists,
    DatasetInDB
)
from synesis_api.auth.schema import User
from synesis_api.auth.service import get_current_user, user_owns_dataset, get_user_from_api_key


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


@router.get("/datasets", response_model=List[Union[DatasetWithObjectGroups, DatasetWithObjectGroupsAndLists]])
async def get_datasets(
    include_object_lists: bool = False,
    user: Annotated[User, Depends(get_current_user)] = None
) -> List[Union[DatasetWithObjectGroups, DatasetWithObjectGroupsAndLists]]:
    """Get all datasets for the current user"""
    return await get_user_datasets(
        user.id,
        include_object_lists=include_object_lists
    )


@router.get("/datasets/{dataset_id}", response_model=Union[DatasetWithObjectGroups, DatasetWithObjectGroupsAndLists])
async def get_dataset_by_id(
    dataset_id: UUID,
    include_object_lists: bool = False,
    user: Annotated[User, Depends(get_current_user)] = None
) -> Union[DatasetWithObjectGroups, DatasetWithObjectGroupsAndLists]:
    """Get a specific dataset by ID"""

    if not await user_owns_dataset(user.id, dataset_id):
        raise HTTPException(
            status_code=403, detail="Not authorized to access this dataset")

    return await get_user_dataset(
        dataset_id,
        user.id,
        include_object_lists=include_object_lists
    )


@router.get("/datasets-by-ids", response_model=List[Union[DatasetWithObjectGroups, DatasetWithObjectGroupsAndLists]])
async def get_datasets_by_ids(
    dataset_ids: List[UUID],
    include_object_lists: bool = False,
    user: Annotated[User, Depends(get_current_user)] = None
) -> List[Union[DatasetWithObjectGroups, DatasetWithObjectGroupsAndLists]]:
    """Get specific datasets by IDs"""
    return await get_user_datasets_by_ids(
        user.id,
        dataset_ids,
        include_object_lists=include_object_lists
    )
