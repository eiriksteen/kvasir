import io
import json
import pandas as pd
from uuid import UUID
from typing import Annotated, List, Union, Dict
from fastapi import APIRouter, Depends, HTTPException, Form, UploadFile, Query

from synesis_api.modules.data_objects.service import get_datasets_service
from kvasir_ontology.entities.dataset.interface import DatasetInterface
from kvasir_ontology.entities.dataset.data_model import (
    Dataset,
    DatasetCreate,
    ObjectGroup,
    ObjectGroupWithObjects,
    DataObject,
    ObjectsFile,
    ObjectGroupCreate,
)
from kvasir_ontology.visualization.data_model import EchartCreate
from synesis_api.auth.service import get_current_user, user_owns_dataset, user_owns_object_group, user_owns_data_object
from synesis_api.auth.schema import User


router = APIRouter()


async def _convert_upload_files_to_dataframes(files: List[UploadFile]) -> Dict[str, pd.DataFrame]:

    filename_to_dataframe = {}
    for file in files:
        content = await file.read()
        df = pd.read_parquet(io.BytesIO(content))
        filename_to_dataframe[file.filename] = df
    return filename_to_dataframe


async def _get_matched_dataframes(
    files: List[UploadFile],
    objects_files: List[ObjectsFile]
) -> Dict[str, pd.DataFrame]:
    filename_to_dataframe = await _convert_upload_files_to_dataframes(files)

    # Verify all required files are present and create filtered mapping
    matched_dataframes = {}
    for objects_file in objects_files:
        if objects_file.filename not in filename_to_dataframe:
            raise HTTPException(
                status_code=400,
                detail=f"File {objects_file.filename} not found in uploaded files"
            )
        matched_dataframes[objects_file.filename] = filename_to_dataframe[objects_file.filename]

    return matched_dataframes


@router.post("/dataset", response_model=Dataset)
async def post_dataset(
    files: List[UploadFile] = None,
    metadata: str = Form(...),
    dataset_service: Annotated[DatasetInterface,
                               Depends(get_datasets_service)] = None
) -> Dataset:

    try:
        dataset_create = DatasetCreate(**json.loads(metadata))
    except Exception as e:
        raise HTTPException(
            status_code=400, detail=f"Invalid metadata: {e}")

    filename_to_dataframe = await _convert_upload_files_to_dataframes(files) if files else None
    return await dataset_service.create_dataset(dataset_create, filename_to_dataframe)


@router.post("/object-group/{dataset_id}", response_model=ObjectGroup)
async def post_object_group(
    dataset_id: UUID,
    files: List[UploadFile] = None,
    metadata: str = Form(...),
    user: Annotated[User, Depends(get_current_user)] = None,
    dataset_service: Annotated[DatasetInterface,
                               Depends(get_datasets_service)] = None
) -> ObjectGroup:

    if not files or len(files) == 0:
        raise HTTPException(
            status_code=400, detail="No files provided")

    if not await user_owns_dataset(user.id, dataset_id):
        raise HTTPException(
            status_code=403, detail="Not authorized to access this dataset")

    try:
        group_create = ObjectGroupCreate(**json.loads(metadata))
    except Exception as e:
        raise HTTPException(
            status_code=400, detail=f"Invalid metadata: {e}")

    group_filename_to_dataframe = await _get_matched_dataframes(files, group_create.objects_files)
    return await dataset_service.add_object_group(dataset_id, group_create, group_filename_to_dataframe)


@router.post("/objects/{group_id}", response_model=List[DataObject])
async def post_objects(
    group_id: UUID,
    files: List[UploadFile] = None,
    metadata: str = Form(...),
    user: Annotated[User, Depends(get_current_user)] = None,
    dataset_service: Annotated[DatasetInterface,
                               Depends(get_datasets_service)] = None
) -> List[DataObject]:

    if not files or len(files) == 0:
        raise HTTPException(
            status_code=400, detail="No files provided")

    if not await user_owns_object_group(user.id, group_id):
        raise HTTPException(
            status_code=403, detail="Not authorized to access this object group")

    try:
        data_list = json.loads(metadata)
        objects_files = [ObjectsFile(**data) for data in data_list]
    except Exception as e:
        raise HTTPException(
            status_code=400, detail=f"Invalid metadata: {e}")

    filename_to_dataframe = await _get_matched_dataframes(files, objects_files)
    return await dataset_service.add_data_objects(group_id, objects_files, filename_to_dataframe)


@router.get("/dataset/{dataset_id}", response_model=Dataset)
async def fetch_dataset(
    dataset_id: UUID,
    dataset_service: Annotated[DatasetInterface, Depends(get_datasets_service)]
) -> Dataset:
    """Get a specific dataset by ID"""
    return await dataset_service.get_dataset(dataset_id)


@router.get("/datasets-by-ids", response_model=List[Dataset])
async def fetch_datasets_by_ids(
    dataset_ids: List[UUID] = Query(...),
    dataset_service: Annotated[DatasetInterface,
                               Depends(get_datasets_service)] = None
) -> List[Dataset]:
    """Get datasets by IDs"""
    return await dataset_service.get_datasets(dataset_ids)


@router.get("/object-group/{group_id}", response_model=Union[ObjectGroup, ObjectGroupWithObjects])
async def fetch_object_group(
    group_id: UUID,
    include_objects: bool = False,
    user: Annotated[User, Depends(get_current_user)] = None,
    dataset_service: Annotated[DatasetInterface,
                               Depends(get_datasets_service)] = None
) -> Union[ObjectGroup, ObjectGroupWithObjects]:
    """Get a specific object group by ID"""

    if not await user_owns_object_group(user.id, group_id):
        raise HTTPException(
            status_code=403, detail="Not authorized to access this object group")

    groups = await dataset_service.get_object_groups(group_ids=[group_id], include_objects=include_objects)
    if not groups:
        raise HTTPException(
            status_code=404, detail="Object group not found")
    return groups[0]


@router.get("/object-groups-in-dataset/{dataset_id}", response_model=List[ObjectGroupWithObjects])
async def fetch_object_groups_in_dataset(
    dataset_id: UUID,
    user: Annotated[User, Depends(get_current_user)] = None,
    dataset_service: Annotated[DatasetInterface,
                               Depends(get_datasets_service)] = None
) -> List[ObjectGroupWithObjects]:
    """Get all object groups in a dataset"""

    if not await user_owns_dataset(user.id, dataset_id):
        raise HTTPException(
            status_code=403, detail="Not authorized to access this dataset")

    groups = await dataset_service.get_object_groups(dataset_id=dataset_id, include_objects=True)
    return groups


@router.get("/data-object/{object_id}", response_model=DataObject)
async def fetch_data_object(
    object_id: UUID,
    user: Annotated[User, Depends(get_current_user)] = None,
    dataset_service: Annotated[DatasetInterface,
                               Depends(get_datasets_service)] = None
) -> DataObject:
    if not await user_owns_data_object(user.id, object_id):
        raise HTTPException(
            status_code=403, detail="Not authorized to access this data object")

    return await dataset_service.get_data_object(object_id)


@router.post("/object-group/{group_id}/echart", response_model=ObjectGroup)
async def create_object_group_echart_endpoint(
    group_id: UUID,
    request: EchartCreate,
    user: Annotated[User, Depends(get_current_user)] = None,
    dataset_service: Annotated[DatasetInterface,
                               Depends(get_datasets_service)] = None
) -> ObjectGroup:
    if not await user_owns_object_group(user.id, group_id):
        raise HTTPException(
            status_code=403, detail="Not authorized to access this object group")

    return await dataset_service.create_object_group_echart(group_id, request)
