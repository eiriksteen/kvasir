from uuid import UUID
from typing import List, Annotated
from fastapi import APIRouter, Depends


from synesis_api.modules.model.service import get_models_service
from kvasir_ontology.entities.model.interface import ModelInterface
from kvasir_ontology.entities.model.data_model import (
    Model,
    ModelCreate,
    ModelImplementationCreate,
    ModelInstantiated,
    ModelInstantiatedCreate,
)

router = APIRouter()


@router.post("/model", response_model=Model)
async def post_model(
    request: ModelCreate,
    model_service: Annotated[ModelInterface, Depends(get_models_service)]
) -> Model:
    return await model_service.create_model(request)


@router.post("/model-implementation", response_model=Model)
async def post_model(
        request: ModelImplementationCreate,
        model_service: Annotated[ModelInterface, Depends(get_models_service)]) -> Model:
    return await model_service.create_model_implementation(request)


@router.post("/model-instantiated", response_model=ModelInstantiated)
async def post_model_instantiated(
    request: ModelInstantiatedCreate,
    model_service: Annotated[ModelInterface, Depends(get_models_service)]
) -> ModelInstantiated:
    return await model_service.create_model_instantiated(request)


@router.get("/models-instantiated-by-ids", response_model=List[ModelInstantiated])
async def fetch_models_instantiated_by_ids(
    model_instantiated_ids: List[UUID],
    model_service: Annotated[ModelInterface, Depends(get_models_service)]
) -> List[ModelInstantiated]:
    return await model_service.get_models_instantiated(model_instantiated_ids)


@router.get("/model-instantiated/{model_instantiated_id}", response_model=ModelInstantiated)
async def get_model_instantiated(
    model_instantiated_id: UUID,
    model_service: Annotated[ModelInterface, Depends(get_models_service)]
) -> ModelInstantiated:
    return await model_service.get_model_instantiated(model_instantiated_id)
