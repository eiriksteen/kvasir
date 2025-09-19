from project_server.client import ProjectClient
from synesis_schemas.main_server import ModelCreate, ModelInDB, ModelEntityCreate, ModelEntityInDB


async def post_model(client: ProjectClient, model_data: ModelCreate) -> ModelInDB:
    """Create a new model"""
    response = await client.send_request("post", "/pipeline/model", json=model_data.model_dump(mode="json"))
    return ModelInDB(**response.body)


async def post_model_entity(client: ProjectClient, model_entity_data: ModelEntityCreate) -> ModelEntityInDB:
    """Create a new model entity"""
    response = await client.send_request("post", "/pipeline/model-entity", json=model_entity_data.model_dump(mode="json"))
    return ModelEntityInDB(**response.body)
