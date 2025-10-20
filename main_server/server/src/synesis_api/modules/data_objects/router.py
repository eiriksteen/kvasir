import json
from uuid import UUID
from typing import Annotated, List, Optional, Union
from datetime import datetime
from fastapi import APIRouter, Depends, HTTPException, Form, UploadFile

from synesis_api.modules.data_objects.service import (
    get_object_groups,
    get_user_dataset_by_id,
    get_object_group,
    create_dataset,
    get_user_datasets,
    get_data_object,
    get_aggregation_object_by_analysis_result_id,
    update_aggregation_object,
    create_aggregation_object

)
# from synesis_api.modules.data_objects.service import get_time_series_payload_data_by_id
from synesis_schemas.main_server import (
    DatasetCreate,
    Dataset,
    GetDatasetsByIDsRequest,
    ObjectGroup,
    ObjectGroupWithObjects,
    DataObjectWithParentGroup,
    DataObject,
    AggregationObjectUpdate,
    AggregationObjectCreate
)
from synesis_schemas.main_server import User
from synesis_data_interface.structures.time_series.schema import TimeSeries
from synesis_api.auth.service import get_current_user, user_owns_dataset, user_owns_object_group, user_owns_data_object
from synesis_api.client import MainServerClient, get_time_series_data
from synesis_api.auth.service import oauth2_scheme

router = APIRouter()


@router.post("/dataset")
async def submit_dataset(
    files: list[UploadFile] = [],
    metadata: str = Form(...),
    user: Annotated[User, Depends(get_current_user)] = None
) -> Dataset:

    try:
        metadata_parsed = DatasetCreate(**json.loads(metadata))
    except Exception as e:
        raise HTTPException(
            status_code=400, detail=f"Invalid metadata: {e}")

    return await create_dataset(files, metadata_parsed, user.id)


@router.get("/dataset/{dataset_id}", response_model=Dataset)
async def fetch_dataset(
    dataset_id: UUID,
    user: Annotated[User, Depends(get_current_user)] = None
) -> Dataset:
    """Get a specific dataset by ID"""
    return await get_user_dataset_by_id(dataset_id, user.id)


@router.get("/datasets-by-ids", response_model=List[Dataset])
async def fetch_datasets_by_ids(
    request: GetDatasetsByIDsRequest,
    user: Annotated[User, Depends(get_current_user)] = None
) -> List[Dataset]:
    """Get a specific dataset by ID"""
    return await get_user_datasets(user.id, dataset_ids=request.dataset_ids, max_features=50)


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

    return await get_object_group(group_id, include_objects=include_objects)


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


@router.get("/data-object/{object_id}", response_model=Union[DataObjectWithParentGroup, DataObject])
async def fetch_data_object(
    object_id: UUID,
    include_object_group: bool = False,
    user: Annotated[User, Depends(get_current_user)] = None
) -> Union[DataObjectWithParentGroup, DataObject]:
    """Get a data object"""

    if not await user_owns_data_object(user.id, object_id):
        raise HTTPException(
            status_code=403, detail="Not authorized to access this data object")

    return await get_data_object(object_id, include_object_group=include_object_group)


@router.get("/time-series-data/{time_series_id}", response_model=TimeSeries)
async def get_time_series_data_from_project_server(
        time_series_id: UUID,
        start_date: Optional[datetime] = None,
        end_date: datetime = datetime.now(),
        user: Annotated[User, Depends(get_current_user)] = None,
        token: str = Depends(oauth2_scheme)) -> TimeSeries:

    if not await user_owns_data_object(user.id, time_series_id):
        raise HTTPException(
            status_code=403, detail="Not authorized to access this data object")

    client = MainServerClient(token)
    time_series = await get_time_series_data(client, time_series_id, start_date, end_date)
    return time_series


@router.post("/aggregation-object")
async def create_aggregation_object_endpoint(
    aggregation_object_create,
    user: Annotated[User, Depends(get_current_user)] = None
):
    aggregation_object = AggregationObjectCreate(**aggregation_object_create) if isinstance(
        aggregation_object_create, dict) else aggregation_object_create
    result = await create_aggregation_object(aggregation_object)
    return result


@router.put("/aggregation-object/{aggregation_object_id}")
async def update_aggregation_object_endpoint(
    aggregation_object_id: UUID,
    aggregation_object_update,
    user: Annotated[User, Depends(get_current_user)] = None
):
    # Shouldnt the ownership be validated here?
    aggregation_update = AggregationObjectUpdate(**aggregation_object_update) if isinstance(
        aggregation_object_update, dict) else aggregation_object_update
    result = await update_aggregation_object(aggregation_object_id, aggregation_update)
    return result


@router.get("/aggregation-object/analysis-result/{analysis_result_id}")
async def get_aggregation_object_by_analysis_result_id_endpoint(
    analysis_result_id: UUID,
    user: Annotated[User, Depends(get_current_user)] = None
):

    result = await get_aggregation_object_by_analysis_result_id(analysis_result_id)
    if result is None:
        raise HTTPException(
            status_code=404, detail="Aggregation object not found")
    return result
