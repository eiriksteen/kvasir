from typing import Annotated, List
from fastapi import APIRouter, Depends, UploadFile
from synesis_api.modules.data_sources.service import (
    create_tabular_file_data_sources,
    fetch_data_sources
)
from synesis_api.modules.data_sources.schema import (
    DataSource,
    TabularFileDataSourceInDB
)
from synesis_api.auth.schema import User
from synesis_api.auth.service import get_current_user
from synesis_api.agents.data_integration.data_source_analysis_agent.runner import run_data_source_analysis_task


router = APIRouter()


# TODO:
# - DB should only commit on end to avoid partial updates
# - Figure out whether to raise http exception in service or just router
# - Possibly simplify structure of router / service / agent


@router.get("/data-sources", response_model=List[DataSource])
async def get_data_sources(
    user: Annotated[User, Depends(get_current_user)] = None
) -> List[DataSource]:
    return await fetch_data_sources(user.id)


@router.post("/file-data-sources", response_model=List[TabularFileDataSourceInDB])
async def file_data_sources(
    files: list[UploadFile],
    user: Annotated[User, Depends(get_current_user)] = None
) -> List[TabularFileDataSourceInDB]:

    # Create base data source records
    data_sources, file_data_sources = await create_tabular_file_data_sources(
        user.id,
        files=files
    )

    # Run agent to populate missing data source fields requiring analysis
    await run_data_source_analysis_task.kiq(
        user.id,
        [data_source.id for data_source in data_sources],
        [file_data_source.file_path for file_data_source in file_data_sources]
    )

    return data_sources
