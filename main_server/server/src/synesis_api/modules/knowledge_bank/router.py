from fastapi import APIRouter

from synesis_api.modules.knowledge_bank.service import search_functions
from synesis_schemas.main_server import (
    SearchFunctionsRequest,
    SearchFunctionsResponse
)


router = APIRouter()


@router.post("/search-functions", response_model=SearchFunctionsResponse)
async def search_functions_endpoint(request: SearchFunctionsRequest) -> SearchFunctionsResponse:
    functions = [await search_functions(query, request.k) for query in request.queries]
    return SearchFunctionsResponse(functions=functions)
