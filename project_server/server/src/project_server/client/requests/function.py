from project_server.client import ProjectClient
from synesis_schemas.main_server import FunctionCreate, FunctionFull, FunctionUpdateCreate, FunctionOutputObjectGroupDefinitionInDB
from uuid import UUID


async def post_function(client: ProjectClient, function_data: FunctionCreate) -> FunctionFull:
    """Create a new function"""
    response = await client.send_request("post", "/function/function", json=function_data.model_dump(mode="json"))
    return FunctionFull(**response.body)


async def post_update_function(client: ProjectClient, function_data: FunctionUpdateCreate) -> FunctionFull:
    """Update a function"""
    response = await client.send_request("post", "/function/function/update", json=function_data.model_dump(mode="json"))
    return FunctionFull(**response.body)
