from typing import List, Union
from uuid import UUID
from fastapi import APIRouter, Depends, HTTPException

from synesis_schemas.main_server import (
    ModelImplementationCreate,
    ModelEntityInDB,
    ModelEntityCreate,
    ModelEntityImplementationCreate,
    ModelEntity,
    User,
    GetModelEntityByIDsRequest,
    ModelEntityConfigUpdate,
    ModelImplementation,
    ModelUpdateCreate
)
from synesis_api.auth.service import get_current_user, user_owns_model_entity, user_can_access_model_source
from synesis_api.modules.model.service import (
    create_model,
    create_model_entity,
    create_model_entity_implementation,
    get_user_model_entities,
    set_new_model_entity_config,
    update_model
)


router = APIRouter()


@router.post("/model", response_model=ModelImplementation)
async def post_model(
    request: ModelImplementationCreate,
    user: User = Depends(get_current_user),
) -> ModelImplementation:
    model = await create_model(user.id, request)
    return model


@router.post("/model/update", response_model=ModelImplementation)
async def post_update_model(
    request: ModelUpdateCreate,
    user: User = Depends(get_current_user),
) -> ModelImplementation:
    model = await update_model(user.id, request)
    return model


@router.post("/model-entity", response_model=ModelEntityInDB)
async def post_model_entity(
    request: ModelEntityCreate,
    user: User = Depends(get_current_user),
) -> ModelEntityInDB:
    """
    Create a bare model entity without implementation.
    This is used when developing or when the exact implementation hasn't been selected yet.
    """
    model_entity = await create_model_entity(user.id, request)
    return model_entity


@router.post("/model-entity-implementation", response_model=ModelEntityInDB)
async def post_model_entity_implementation(
    request: ModelEntityImplementationCreate,
    user: User = Depends(get_current_user),
) -> ModelEntityInDB:
    """
    Create a model entity implementation.
    This creates or uses an existing model entity and attaches a model implementation with config.
    """
    model_entity = await create_model_entity_implementation(user.id, request)
    return model_entity


@router.get("/model-entities-by-ids", response_model=List[ModelEntity])
async def fetch_model_entities_by_ids(
    request: GetModelEntityByIDsRequest,
    user: User = Depends(get_current_user),
) -> List[ModelEntity]:

    # TODO: Should add user id field to model entity to enable auth
    return await get_user_model_entities(user.id, request.model_entity_ids)


@router.patch("/model-entity/{model_entity_id}/config", response_model=ModelEntity)
async def patch_model_entity_config(
    model_entity_id: UUID,
    request: ModelEntityConfigUpdate,
    user: User = Depends(get_current_user),
) -> ModelEntity:
    """Update the config of a model entity implementation."""
    if not await user_owns_model_entity(user.id, model_entity_id):
        raise HTTPException(
            status_code=403, detail="Not authorized to access this model entity")

    return await set_new_model_entity_config(user.id, model_entity_id, request)
