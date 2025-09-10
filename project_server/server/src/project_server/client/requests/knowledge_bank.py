from project_server.client import ProjectClient
from synesis_schemas.main_server import SearchFunctionsRequest, SearchFunctionsResponse


async def post_search_functions(client: ProjectClient, request: SearchFunctionsRequest) -> SearchFunctionsResponse:
    response = await client.send_request("post", "/knowledge-bank/search-functions", json=request.model_dump(mode="json"))
    return SearchFunctionsResponse(**response.body)
