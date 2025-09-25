from fastapi import APIRouter, Depends
from typing import List
from uuid import UUID

from synesis_api.auth.service import get_current_user
from synesis_schemas.main_server import User
from synesis_api.modules.pipeline.service import get_project_pipelines, create_pipeline, get_user_pipelines_by_ids
from synesis_schemas.main_server import PipelineFull, PipelineCreate, PipelineInDB

router = APIRouter()


@router.get("/project-pipelines/{project_id}", response_model=List[PipelineFull])
async def fetch_pipelines(project_id: UUID, user: User = Depends(get_current_user)) -> List[PipelineInDB]:
    pipelines = await get_project_pipelines(user.id, project_id)
    return pipelines


@router.get("/user-pipeline/{pipeline_id}", response_model=PipelineFull)
async def fetch_pipeline(
    pipeline_id: str,
    user: User = Depends(get_current_user),
) -> PipelineFull:

    pipe = await get_user_pipelines_by_ids(user.id, [pipeline_id])
    return pipe[0]


@router.post("/pipeline", response_model=PipelineInDB)
async def post_pipeline(
    request: PipelineCreate,
    user: User = Depends(get_current_user),
) -> PipelineInDB:

    pipeline = await create_pipeline(user.id, request)
    return pipeline
