from typing import List
from uuid import UUID

from project_server.client import ProjectClient
from synesis_schemas.main_server import (
    ModelImplementationCreate,
    ModelEntityCreate,
    ModelEntityImplementationCreate,
    ModelEntityInDB,
    GetModelEntityByIDsRequest,
    ModelEntity,
    ModelEntityConfigUpdate,
    ModelImplementation,
    ModelUpdateCreate,
)


async def post_model(client: ProjectClient, model_data: ModelImplementationCreate) -> ModelImplementation:
    response = await client.send_request("post", "/model/model", json=model_data.model_dump(mode="json"))
    return ModelImplementation(**response.body)


async def post_update_model(client: ProjectClient, request: ModelUpdateCreate) -> ModelImplementation:
    response = await client.send_request("post", f"/model/model/update", json=request.model_dump(mode="json"))
    return ModelImplementation(**response.body)


async def post_model_entity(client: ProjectClient, model_entity_data: ModelEntityCreate) -> ModelEntityInDB:
    """Create a bare model entity without implementation."""
    response = await client.send_request("post", "/model/model-entity", json=model_entity_data.model_dump(mode="json"))
    return ModelEntityInDB(**response.body)


async def post_model_entity_implementation(client: ProjectClient, model_entity_impl_data: ModelEntityImplementationCreate) -> ModelEntityInDB:
    """Create a model entity implementation (entity + implementation + config)."""
    response = await client.send_request("post", "/model/model-entity-implementation", json=model_entity_impl_data.model_dump(mode="json"))
    return ModelEntityInDB(**response.body)


async def get_project_model_entities(client: ProjectClient, project_id: UUID) -> List[ModelEntity]:
    response = await client.send_request("get", f"/project/project-model-entities/{project_id}")
    return [ModelEntity(**me) for me in response.body]


async def get_model_entities_by_ids(client: ProjectClient, request: GetModelEntityByIDsRequest) -> List[ModelEntity]:
    response = await client.send_request("get", f"/model/model-entities-by-ids", json=request.model_dump(mode="json"))
    return [ModelEntity(**me) for me in response.body]


async def patch_model_entity_config(client: ProjectClient, model_entity_id: UUID, request: ModelEntityConfigUpdate) -> ModelEntityInDB:
    response = await client.send_request("patch", f"/model/model-entity/{model_entity_id}/config", json=request.model_dump(mode="json"))
    return ModelEntityInDB(**response.body)
