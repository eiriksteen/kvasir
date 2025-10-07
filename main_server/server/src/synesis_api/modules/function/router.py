from fastapi import APIRouter, Depends

from synesis_schemas.main_server import FunctionFull, FunctionCreate, FunctionUpdateCreate
from synesis_api.auth.service import get_current_user
from synesis_api.modules.function.service import create_function, update_function
from uuid import UUID
from synesis_schemas.main_server import User

router = APIRouter()


@router.post("/function", response_model=FunctionFull)
async def post_function(
    request: FunctionCreate,
    _: User = Depends(get_current_user),
) -> FunctionFull:

    function = await create_function(request)
    return function


@router.post("/function/update", response_model=FunctionFull)
async def post_update_function(
    request: FunctionUpdateCreate,
    _: User = Depends(get_current_user),
) -> FunctionFull:
    function = await update_function(request)
    return function
