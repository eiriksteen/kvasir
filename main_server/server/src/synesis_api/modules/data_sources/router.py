from uuid import UUID
from typing import Annotated, List, Union
from fastapi import APIRouter, Depends, UploadFile, HTTPException

from synesis_api.modules.data_sources.service import (
    create_data_source,
    get_data_sources,
    create_data_source_analysis,
    create_data_source_details
)
from synesis_schemas.main_server import (
    DataSourceInDB,
    DataSource,
    DataSourceAnalysisInDB,
    DataSourceAnalysisCreate,
    TabularFileDataSource,
    TabularFileDataSourceCreate,
    TabularFileDataSourceInDB
)
from synesis_schemas.project_server import RunDataSourceAnalysisRequest
from synesis_schemas.main_server import User
from synesis_api.auth.service import get_current_user, user_owns_data_source
# from synesis_api.agents.data_source_analysis.runner import run_data_source_analysis_task
from synesis_api.auth.service import oauth2_scheme
from synesis_api.client import MainServerClient, post_run_data_source_analysis, post_file


router = APIRouter()


# TODO:
# - DB should only commit on end to avoid partial updates
# - Figure out whether to raise http exception in service or just router
# - Possibly simplify structure of router / service / agent


@router.get("/data-sources", response_model=List[DataSource])
async def fetch_data_sources(
    user: Annotated[User, Depends(get_current_user)] = None
) -> List[DataSource]:
    return await get_data_sources(user_id=user.id)


@router.get("/data-sources-by-ids", response_model=List[DataSource])
async def fetch_data_sources_by_ids(
    data_source_ids: List[UUID],
    user: Annotated[User, Depends(get_current_user)] = None
) -> List[DataSource]:
    return await get_data_sources(data_source_ids=data_source_ids, user_id=user.id)


@router.post("/file-data-source", response_model=DataSourceInDB)
async def post_file_data_source(
        file: UploadFile,
        user: Annotated[User, Depends(get_current_user)] = None,
        token: str = Depends(oauth2_scheme)) -> DataSourceInDB:

    data_source_record = await create_data_source(user.id, type="file", name=file.filename)
    file_content = await file.read()

    client = MainServerClient(token)
    file_response = await post_file(client, file_content, data_source_record.id)

    # Run agent to populate missing data source fields requiring analysis
    await post_run_data_source_analysis(client, RunDataSourceAnalysisRequest(
        data_source_id=data_source_record.id,
        file_path=file_response.file_path
    ))

    return data_source_record


@router.post("/data-source-analysis", response_model=DataSourceAnalysisInDB)
async def post_data_source_analysis(
        analysis: DataSourceAnalysisCreate,
        user: Annotated[User, Depends(get_current_user)] = None) -> DataSourceAnalysisInDB:

    if not await user_owns_data_source(user.id, analysis.data_source_id):
        raise HTTPException(
            status_code=403, detail="You do not have permission to access this data source")

    return await create_data_source_analysis(analysis)


@router.post("/data-source-details", response_model=Union[TabularFileDataSourceInDB])
async def post_data_source_details(
        details: Union[TabularFileDataSourceCreate],
        user: Annotated[User, Depends(get_current_user)] = None) -> Union[TabularFileDataSourceInDB]:

    if not await user_owns_data_source(user.id, details.data_source_id):
        raise HTTPException(
            status_code=403, detail="You do not have permission to access this data source")

    return await create_data_source_details(details)
