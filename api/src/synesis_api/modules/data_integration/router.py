import uuid
from typing import Annotated
from fastapi import APIRouter, Depends, HTTPException, UploadFile, Form
from synesis_api.modules.data_integration.service import (
    get_job_results_from_job_id,
    create_local_directory_data_source
)
from synesis_api.modules.data_integration.schema import (
    IntegrationJobResult,
    LocalDirectoryDataSource
)
from synesis_api.auth.schema import User
from synesis_api.auth.service import (get_current_user,
                                      user_owns_job)
from synesis_api.modules.jobs.service import get_job

data_integration_router = APIRouter()


# TODO:
# - DB should only commit on end to avoid partial updates
# - Figure out whether to raise http exception in service or just router
# - Possibly simplify structure of router / service / agent


@data_integration_router.post("/local-directory-data-source", response_model=LocalDirectoryDataSource)
async def local_directory_data_source(
    files: list[UploadFile],
    directory_name: str = Form(...),
    description: str = Form(...),
    user: Annotated[User, Depends(get_current_user)] = None
) -> LocalDirectoryDataSource:

    data_source = await create_local_directory_data_source(
        directory_name,
        description,
        user.id,
        files)

    return data_source


@data_integration_router.get("/integration-job-results/{job_id}", response_model=IntegrationJobResult)
async def get_integration_job_results(
    job_id: uuid.UUID,
    user: Annotated[User, Depends(get_current_user)] = None
) -> IntegrationJobResult:

    if not user or not await user_owns_job(user.id, job_id):
        raise HTTPException(
            status_code=403, detail="You do not have permission to access this job")

    job_metadata = await get_job(job_id)

    if job_metadata.status == "completed":
        return await get_job_results_from_job_id(job_id)
    else:
        raise HTTPException(
            status_code=202, detail="Integration job is still running")
