from typing import List

from project_server.client import ProjectClient
from synesis_schemas.main_server import FunctionCreate, Function, FunctionUpdateCreate, GetFunctionsRequest


async def post_function(client: ProjectClient, function_data: FunctionCreate) -> Function:
    """Create a new function"""
    response = await client.send_request("post", "/function/function", json=function_data.model_dump(mode="json"))
    return Function(**response.body)


async def post_update_function(client: ProjectClient, function_data: FunctionUpdateCreate) -> Function:
    """Update a function"""
    response = await client.send_request("post", "/function/function/update", json=function_data.model_dump(mode="json"))
    return Function(**response.body)


async def get_functions(client: ProjectClient, request: GetFunctionsRequest) -> List[Function]:
    """Get functions"""
    response = await client.send_request("post", "/function/get-functions", json=request.model_dump(mode="json"))
    return [Function(**f) for f in response.body]
