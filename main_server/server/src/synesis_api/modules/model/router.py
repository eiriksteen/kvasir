from fastapi import APIRouter, Depends, HTTPException
from uuid import UUID
from typing import List

from synesis_schemas.main_server import (
    ModelCreate,
    ModelEntityInDB,
    ModelEntityCreate,
    ModelEntity,
    User,
    GetModelEntityByIDsRequest,
    ModelEntityConfigUpdate,
    Model,
    ModelUpdateCreate
)
from synesis_api.auth.service import get_current_user, user_owns_project, user_owns_model_entity
from synesis_api.modules.model.service import create_model, create_model_entity, get_project_model_entities, get_user_model_entities_by_ids, set_new_model_entity_config, update_model


router = APIRouter()


@router.post("/model", response_model=Model)
async def post_model(
    request: ModelCreate,
    user: User = Depends(get_current_user),
) -> Model:
    model = await create_model(user.id, request)
    return model


@router.post("/model/update", response_model=Model)
async def post_update_model(
    request: ModelUpdateCreate,
    user: User = Depends(get_current_user),
) -> Model:
    model = await update_model(user.id, request)
    return model


@router.post("/model-entity", response_model=ModelEntityInDB)
async def post_model_entity(
    request: ModelEntityCreate,
    user: User = Depends(get_current_user),
) -> ModelEntityInDB:

    model_entity = await create_model_entity(user.id, request)
    return model_entity


@router.get("/project-model-entities/{project_id}", response_model=List[ModelEntity])
async def fetch_project_model_entities(
    project_id: UUID,
    user: User = Depends(get_current_user),
) -> List[ModelEntity]:

    if not await user_owns_project(user.id, project_id):
        raise HTTPException(
            status_code=403, detail="Not authorized to access this project")

    return await get_project_model_entities(user.id, project_id)


@router.get("/model-entities-by-ids", response_model=List[ModelEntity])
async def fetch_model_entities_by_ids(
    request: GetModelEntityByIDsRequest,
    user: User = Depends(get_current_user),
) -> List[ModelEntity]:

    # TODO: Should add user id field to model entity to enable auth
    return await get_user_model_entities_by_ids(user.id, request.model_entity_ids)


@router.patch("/model-entity/{model_entity_id}/config", response_model=ModelEntityInDB)
async def patch_model_entity_config(
    model_entity_id: UUID,
    request: ModelEntityConfigUpdate,
    user: User = Depends(get_current_user),
) -> ModelEntityInDB:
    if not await user_owns_model_entity(user.id, model_entity_id):
        raise HTTPException(
            status_code=403, detail="Not authorized to access this model entity")

    return await set_new_model_entity_config(user.id, model_entity_id, request)
