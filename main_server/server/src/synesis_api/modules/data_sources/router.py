from typing import Annotated, List
from fastapi import APIRouter, Depends, UploadFile, HTTPException
from uuid import UUID

from synesis_api.modules.data_sources.service import (
    create_tabular_file_data_source,
    create_key_value_data_source,
    get_user_data_sources,
    create_data_source_analysis
)
from synesis_schemas.main_server import (
    DataSourceInDB,
    DataSource,
    DataSourceAnalysisInDB,
    DataSourceAnalysisCreate,
    GetDataSourcesByIDsRequest,
    TabularFileDataSourceInDB,
    KeyValueFileDataSourceInDB
)
# from synesis_schemas.project_server import RunDataSourceAnalysisAgentRequest
from synesis_schemas.main_server import User
from synesis_api.auth.service import get_current_user, user_owns_data_source
from synesis_api.auth.service import oauth2_scheme
from synesis_api.client import MainServerClient, post_tabular_file_data_source, post_key_value_file_data_source


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


@router.post("/tabular-file-data-source", response_model=DataSource)
async def post_tabular_file_data_source_endpoint(
        file: UploadFile,
        user: Annotated[User, Depends(get_current_user)] = None,
        token: str = Depends(oauth2_scheme)) -> DataSource:

    file_content = await file.read()
    client = MainServerClient(token)
    data_source_create = await post_tabular_file_data_source(
        client,
        file_content,
        file.filename,
        file.content_type
    )
    result = await create_tabular_file_data_source(user.id, data_source_create)

    return result


@router.post("/key-value-file-data-source", response_model=DataSource)
async def post_key_value_file_data_source_endpoint(
        file: UploadFile,
        user: Annotated[User, Depends(get_current_user)] = None,
        token: str = Depends(oauth2_scheme)) -> DataSource:

    file_content = await file.read()
    client = MainServerClient(token)
    data_source_create = await post_key_value_file_data_source(
        client,
        file_content,
        file.filename or "unknown",
        file.content_type or "application/octet-stream"
    )
    result = await create_key_value_data_source(user.id, data_source_create)

    return result


@router.post("/data-source-analysis", response_model=DataSourceAnalysisInDB)
async def post_data_source_analysis(
        analysis: DataSourceAnalysisCreate,
        user: Annotated[User, Depends(get_current_user)] = None) -> DataSourceAnalysisInDB:

    if not await user_owns_data_source(user.id, analysis.data_source_id):
        raise HTTPException(
            status_code=403, detail="You do not have permission to access this data source")

    return await create_data_source_analysis(analysis)
