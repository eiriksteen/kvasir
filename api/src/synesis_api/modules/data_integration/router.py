import uuid
from typing import Annotated, List
from fastapi import APIRouter, Depends, HTTPException, UploadFile
from synesis_api.modules.data_integration.service import (
    get_job_results_from_job_id,
    create_tabular_file_data_sources,
    fetch_data_sources
)
from synesis_api.modules.data_integration.schema import (
    DataIntegrationJobResultInDB,
    DataSource,
    TabularFileDataSourceInDB
)
from synesis_api.auth.schema import User
from synesis_api.auth.service import get_current_user, user_owns_job
from synesis_api.modules.jobs.service import get_job
from synesis_api.agents.data_integration.data_source_analysis_agent.runner import run_data_source_analysis_task


data_integration_router = APIRouter()


# TODO:
# - DB should only commit on end to avoid partial updates
# - Figure out whether to raise http exception in service or just router
# - Possibly simplify structure of router / service / agent


@data_integration_router.get("/data-sources", response_model=List[DataSource])
async def get_data_sources(
    user: Annotated[User, Depends(get_current_user)] = None
) -> List[DataSource]:
    return await fetch_data_sources(user.id)


@data_integration_router.post("/file-data-sources", response_model=List[TabularFileDataSourceInDB])
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


@data_integration_router.get("/integration-job-results/{job_id}", response_model=DataIntegrationJobResultInDB)
async def get_integration_job_results(
    job_id: uuid.UUID,
    user: Annotated[User, Depends(get_current_user)] = None
) -> DataIntegrationJobResultInDB:

    if not user or not await user_owns_job(user.id, job_id):
        raise HTTPException(
            status_code=403, detail="You do not have permission to access this job")

    job_metadata = await get_job(job_id)

    if job_metadata.status == "completed":
        return await get_job_results_from_job_id(job_id)
    else:
        raise HTTPException(
            status_code=202, detail="Integration job is still running")
