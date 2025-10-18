from uuid import UUID
from typing import List, Union
from fastapi import APIRouter, Depends, HTTPException

from synesis_schemas.main_server import (
    ModelCreate,
    ModelEntityInDB,
    ModelEntityCreate,
    ModelEntity,
    User,
    GetModelEntityByIDsRequest,
    ModelEntityConfigUpdate,
    Model,
    ModelUpdateCreate,
    ModelSource,
    PypiModelSourceCreate
)
from synesis_api.auth.service import get_current_user, user_owns_model_entity
from synesis_api.modules.model.service import (
    create_model,
    create_model_entity,
    get_user_model_entities,
    set_new_model_entity_config,
    update_model,
    create_model_source,
    get_model_sources_by_ids,
)
from synesis_api.auth.service import user_can_access_model_source


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


@router.get("/model-entities-by-ids", response_model=List[ModelEntity])
async def fetch_model_entities_by_ids(
    request: GetModelEntityByIDsRequest,
    user: User = Depends(get_current_user),
) -> List[ModelEntity]:

    # TODO: Should add user id field to model entity to enable auth
    return await get_user_model_entities(user.id, request.model_entity_ids)


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


@router.post("/model-source", response_model=ModelSource)
async def post_model_source(
    request: Union[PypiModelSourceCreate],
    user: User = Depends(get_current_user)
) -> ModelSource:
    return await create_model_source(user.id, request)


@router.get("/model-source/{model_source_id}", response_model=ModelSource)
async def fetch_model_source_by_id(
    model_source_id: UUID,
    user: User = Depends(get_current_user)
) -> ModelSource:

    if not await user_can_access_model_source(user.id, model_source_id):
        raise HTTPException(
            status_code=403, detail="You do not have permission to access this model source")

    return (await get_model_sources_by_ids(user.id, [model_source_id]))[0]
