from fastapi import APIRouter, Depends

from synesis_schemas.main_server import Function, FunctionCreate, FunctionUpdateCreate
from synesis_api.auth.service import get_current_user
from synesis_api.modules.function.service import create_function, update_function
from uuid import UUID
from synesis_schemas.main_server import User

router = APIRouter()


@router.post("/function", response_model=Function)
async def post_function(
    request: FunctionCreate,
    user: User = Depends(get_current_user),
) -> Function:

    function = await create_function(user.id, request)
    return function


@router.post("/function/update", response_model=Function)
async def post_update_function(
    request: FunctionUpdateCreate,
    user: User = Depends(get_current_user),
) -> Function:
    function = await update_function(user.id, request)
    return function
