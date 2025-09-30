from project_server.client import ProjectClient
from synesis_schemas.main_server import FunctionCreate, FunctionBare, FunctionUpdateCreate


async def post_function(client: ProjectClient, function_data: FunctionCreate) -> FunctionBare:
    """Create a new function"""
    response = await client.send_request("post", "/function/function", json=function_data.model_dump(mode="json"))
    return FunctionBare(**response.body)


async def post_update_function(client: ProjectClient, function_data: FunctionUpdateCreate) -> FunctionBare:
    """Update a function"""
    response = await client.send_request("post", "/function/function/update", json=function_data.model_dump(mode="json"))
    return FunctionBare(**response.body)
