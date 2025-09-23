from fastapi import APIRouter, Depends, HTTPException
from uuid import UUID
from typing import List

from synesis_schemas.main_server import ModelInDB, ModelCreate, ModelEntityInDB, ModelEntityCreate, ModelEntityFull, User
from synesis_api.auth.service import get_current_user, user_owns_project
from synesis_api.modules.model.service import create_model, create_model_entity, get_project_model_entities


router = APIRouter()


@router.post("/model", response_model=ModelInDB)
async def post_model(
    request: ModelCreate,
    user: User = Depends(get_current_user),
) -> ModelInDB:
    model = await create_model(user.id, request)
    return model


@router.post("/model-entity", response_model=ModelEntityInDB)
async def post_model_entity(
    request: ModelEntityCreate,
    user: User = Depends(get_current_user),
) -> ModelEntityInDB:

    if not await user_owns_project(user.id, request.project_id):
        raise HTTPException(
            status_code=403, detail="Not authorized to modify this project")

    model_entity = await create_model_entity(request)
    return model_entity


@router.get("/project-model-entities/{project_id}", response_model=List[ModelEntityFull])
async def fetch_project_model_entities(
    project_id: UUID,
    user: User = Depends(get_current_user),
) -> List[ModelEntityFull]:

    if not await user_owns_project(user.id, project_id):
        raise HTTPException(
            status_code=403, detail="Not authorized to access this project")

    return await get_project_model_entities(project_id)
