from project_server.client import ProjectClient
from synesis_schemas.main_server import FunctionCreate, FunctionInDB


async def post_function(client: ProjectClient, function_data: FunctionCreate) -> FunctionInDB:
    """Create a new function"""
    response = await client.send_request("post", "/pipeline/function", json=function_data.model_dump(mode="json"))
    return FunctionInDB(**response.body)
