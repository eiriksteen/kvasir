from fastapi import APIRouter

from synesis_api.modules.knowledge_bank.service import query_functions
from synesis_schemas.main_server import (
    SearchFunctionsRequest,
    SearchFunctionsResponse
)


router = APIRouter()


@router.post("/search-functions", response_model=SearchFunctionsResponse)
async def search_functions_endpoint(request: SearchFunctionsRequest) -> SearchFunctionsResponse:
    results = []
    for query in request.queries:
        results.append(await query_functions(query))
    return SearchFunctionsResponse(results=results)
