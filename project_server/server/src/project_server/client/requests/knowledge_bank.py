from typing import List


from project_server.client import ProjectClient
from synesis_schemas.main_server import SearchFunctionsRequest, SearchModelsRequest, FunctionQueryResult, ModelQueryResult, GetGuidelinesRequest


async def post_search_functions(client: ProjectClient, request: SearchFunctionsRequest) -> List[FunctionQueryResult]:
    response = await client.send_request("post", "/knowledge-bank/search-functions", json=request.model_dump(mode="json"))
    results = [FunctionQueryResult(**r) for r in response.body]
    return results


async def post_search_models(client: ProjectClient, request: SearchModelsRequest) -> List[ModelQueryResult]:
    response = await client.send_request("post", "/knowledge-bank/search-models", json=request.model_dump(mode="json"))
    results = [ModelQueryResult(**r) for r in response.body]
    return results


async def get_task_guidelines(client: ProjectClient, request: GetGuidelinesRequest) -> str:
    response = await client.send_request("get", "/knowledge-bank/task-guidelines", json=request.model_dump(mode="json"))
    return response.body
