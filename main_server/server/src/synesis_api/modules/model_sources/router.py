import uuid
from typing import Union, List
from fastapi import APIRouter, Depends, HTTPException

from synesis_schemas.main_server import PypiModelSourceCreate, PypiModelSourceInDB, ModelSource
from synesis_api.auth.service import get_current_user, user_can_access_model_source
from synesis_api.modules.model_sources.service import create_model_source, get_model_sources_by_ids, get_project_model_sources
from synesis_schemas.main_server import User


router = APIRouter()


@router.post("/model-source", response_model=ModelSource)
async def post_model_source(
    request: Union[PypiModelSourceCreate],
    user: User = Depends(get_current_user)
) -> ModelSource:
    return await create_model_source(user.id, request)


@router.get("/project-model-sources/{project_id}", response_model=List[ModelSource])
async def fetch_project_model_sources(
    project_id: uuid.UUID,
    user: User = Depends(get_current_user)
) -> List[ModelSource]:
    return await get_project_model_sources(user.id, project_id)


@router.get("/model-source/{model_source_id}", response_model=ModelSource)
async def fetch_model_source_by_id(
    model_source_id: uuid.UUID,
    user: User = Depends(get_current_user)
) -> ModelSource:

    if not await user_can_access_model_source(user.id, model_source_id):
        raise HTTPException(
            status_code=403, detail="You do not have permission to access this model source")

    return (await get_model_sources_by_ids(user.id, [model_source_id]))[0]
