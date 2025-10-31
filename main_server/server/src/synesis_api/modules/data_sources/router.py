from typing import Annotated, List
from fastapi import APIRouter, Depends
from uuid import UUID

from synesis_api.modules.data_sources.service import (
    create_file_data_source,
    get_user_data_sources,
)
from synesis_schemas.main_server import (
    DataSource,
    GetDataSourcesByIDsRequest,
    FileDataSourceCreate
)
from synesis_schemas.main_server import User
from synesis_api.auth.service import get_current_user


router = APIRouter()


# TODO:
# - DB should only commit on end to avoid partial updates
# - Figure out whether to raise http exception in service or just router
# - Possibly simplify structure of router / service / agent


@router.get("/data-sources", response_model=List[DataSource])
async def fetch_data_sources(
    user: Annotated[User, Depends(get_current_user)] = None
) -> List[DataSource]:
    return await get_user_data_sources(user_id=user.id)


@router.get("/data-source/{data_source_id}", response_model=DataSource)
async def fetch_data_source(
    data_source_id: UUID,
    user: Annotated[User, Depends(get_current_user)] = None
) -> DataSource:
    return (await get_user_data_sources(user_id=user.id, data_source_ids=[data_source_id]))[0]


@router.get("/data-sources-by-ids", response_model=List[DataSource])
async def fetch_data_sources_by_ids(
    request: GetDataSourcesByIDsRequest,
    user: Annotated[User, Depends(get_current_user)] = None
) -> List[DataSource]:
    return await get_user_data_sources(data_source_ids=request.data_source_ids, user_id=user.id)


@router.post("/file-data-source", response_model=DataSource)
async def create_file_data_source_endpoint(
    file_data_source_create: FileDataSourceCreate,
    user: Annotated[User, Depends(get_current_user)] = None
) -> DataSource:
    """Create a file data source (used by agents to add FileDataSourceInDB)"""
    return await create_file_data_source(user.id, file_data_source_create)
