from fastapi import APIRouter, Depends
from typing import List, Union

from synesis_api.modules.knowledge_bank.service import query_functions, query_models, get_task_guidelines

from synesis_schemas.main_server import (
    SearchFunctionsRequest,
    FunctionQueryResult,
    SearchModelsRequest,
    ModelQueryResult,
    GetGuidelinesRequest,
    FunctionQueryResultBare,
    ModelQueryResultBare,
)
from synesis_api.auth.service import get_current_user
from synesis_schemas.main_server import User


router = APIRouter()


# All or some of these should maybe be turned into MCP?


@router.post("/search-functions", response_model=List[Union[FunctionQueryResult, FunctionQueryResultBare]])
async def search_functions_endpoint(
    request: SearchFunctionsRequest,
    _: User = Depends(get_current_user)
) -> List[Union[FunctionQueryResult, FunctionQueryResultBare]]:
    return await query_functions(request)


@router.post("/search-models", response_model=List[Union[ModelQueryResult, ModelQueryResultBare]])
async def search_models_endpoint(request: SearchModelsRequest, user: User = Depends(get_current_user)) -> List[Union[ModelQueryResult, ModelQueryResultBare]]:
    return await query_models(user.id, request)


@router.get("/task-guidelines", response_model=str)
async def get_task_guidelines_endpoint(
    request: GetGuidelinesRequest,
    _: User = Depends(get_current_user)
) -> str:
    return get_task_guidelines(request)
