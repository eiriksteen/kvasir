from fastapi import APIRouter
from typing import List

from synesis_api.modules.knowledge_bank.service import query_functions, query_models, query_model_sources

from synesis_schemas.main_server import (
    SearchFunctionsRequest,
    FunctionQueryResult,
    SearchModelsRequest,
    ModelQueryResult,
    SearchModelSourcesRequest,
    ModelSourceQueryResult,
)


router = APIRouter()


@router.post("/search-functions", response_model=List[FunctionQueryResult])
async def search_functions_endpoint(request: SearchFunctionsRequest) -> List[FunctionQueryResult]:
    results = []
    for query in request.queries:
        results.append(await query_functions(query))
    return results


@router.post("/search-models", response_model=List[ModelQueryResult])
async def search_models_endpoint(request: SearchModelsRequest) -> List[ModelQueryResult]:
    results = []
    for query in request.queries:
        results.append(await query_models(query))
    return results


@router.post("/search-model-sources", response_model=List[ModelSourceQueryResult])
async def search_model_sources_endpoint(request: SearchModelSourcesRequest) -> List[ModelSourceQueryResult]:
    results = []
    for query in request.queries:
        results.append(await query_model_sources(query))
    return results
