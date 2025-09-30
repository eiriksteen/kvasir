from fastapi import APIRouter, Depends
from typing import List

from synesis_api.modules.knowledge_bank.service import query_functions, query_models

from synesis_schemas.main_server import (
    SearchFunctionsRequest,
    FunctionQueryResult,
    SearchModelsRequest,
    ModelQueryResult,
)
from synesis_api.auth.service import get_current_user
from synesis_schemas.main_server import User


router = APIRouter()


@router.post("/search-functions", response_model=List[FunctionQueryResult])
async def search_functions_endpoint(
    request: SearchFunctionsRequest,
    _: User = Depends(get_current_user)
) -> List[FunctionQueryResult]:
    results = []
    for query in request.queries:
        results.append(await query_functions(query))
    return results


@router.post("/search-models", response_model=List[ModelQueryResult])
async def search_models_endpoint(request: SearchModelsRequest, user: User = Depends(get_current_user)) -> List[ModelQueryResult]:
    results = []
    for query in request.queries:
        results.append(await query_models(user.id, query))
    return results
