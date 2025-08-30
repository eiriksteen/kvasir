from fastapi import APIRouter, Depends, HTTPException
from synesis_api.auth.service import get_current_user
from synesis_api.auth.schema import User
from synesis_api.modules.pipeline.service import get_user_pipelines, get_user_pipeline_with_functions
from synesis_api.modules.pipeline.schema import PipelineFull

router = APIRouter()


@router.get("/user-pipelines")
async def fetch_pipelines(
    user: User = Depends(get_current_user),
):
    pipelines = await get_user_pipelines(user.id)

    return pipelines


@router.get("/user-pipeline/{pipeline_id}")
async def fetch_pipeline(
    pipeline_id: str,
    user: User = Depends(get_current_user),
) -> PipelineFull:

    pipe = await get_user_pipeline_with_functions(user.id, pipeline_id)

    return pipe
