import uuid
from typing import Annotated
from fastapi import APIRouter, Depends, HTTPException
from synesis_api.modules.model_integration.service import (
    get_model_integration_job_results,
)
from synesis_api.modules.model_integration.schema import (
    ModelIntegrationJobResult,
    ModelIntegrationJobInput
)
from synesis_api.agents.model_integration.runner import run_model_integration_task
from synesis_api.modules.jobs.schema import Job
from synesis_api.auth.schema import User
from synesis_api.auth.service import get_current_user, user_owns_job
from synesis_api.modules.jobs.service import get_job, create_job

router = APIRouter()


@router.get("/model-integration-job-results/{job_id}", response_model=ModelIntegrationJobResult)
async def get_model_integration_job_results(
    job_id: uuid.UUID,
    user: Annotated[User, Depends(get_current_user)] = None
) -> ModelIntegrationJobResult:

    if not user or not await user_owns_job(user.id, job_id):
        raise HTTPException(
            status_code=403, detail="You do not have permission to access this job")

    job_metadata = await get_job(job_id)

    if job_metadata.status != "completed":
        raise HTTPException(
            status_code=400, detail="Model integration job is not completed yet")

    try:
        results = await get_model_integration_job_results(job_id)
        return results
    except Exception as e:
        raise HTTPException(
            status_code=404, detail=f"Model integration results not found: {str(e)}")
