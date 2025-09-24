from typing import List
from uuid import UUID

from project_server.client import ProjectClient
from synesis_schemas.main_server import ModelCreate, ModelInDB, ModelEntityCreate, ModelEntityInDB, GetModelEntityByIDsRequest, ModelEntityFull


async def post_model(client: ProjectClient, model_data: ModelCreate) -> ModelInDB:
    """Create a new model"""
    response = await client.send_request("post", "/model/model", json=model_data.model_dump(mode="json"))
    return ModelInDB(**response.body)


async def post_model_entity(client: ProjectClient, model_entity_data: ModelEntityCreate) -> ModelEntityInDB:
    """Create a new model entity"""
    response = await client.send_request("post", "/model/model-entity", json=model_entity_data.model_dump(mode="json"))
    return ModelEntityInDB(**response.body)


async def get_project_model_entities(client: ProjectClient, project_id: UUID) -> List[ModelEntityFull]:
    response = await client.send_request("get", f"/model/project-model-entities/{project_id}")
    return [ModelEntityFull(**me) for me in response.body]


async def get_model_entities_by_ids(client: ProjectClient, request: GetModelEntityByIDsRequest) -> List[ModelEntityFull]:
    response = await client.send_request("get", f"/model/model-entities-by-ids", json=request.model_dump(mode="json"))
    return [ModelEntityFull(**me) for me in response.body]
