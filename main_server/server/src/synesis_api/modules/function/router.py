from fastapi import APIRouter, Depends

from synesis_schemas.main_server import FunctionInDB, FunctionCreate
from synesis_api.auth.service import get_current_user
from synesis_api.modules.function.service import create_function
from synesis_schemas.main_server import User

router = APIRouter()


@router.post("/function", response_model=FunctionInDB)
async def post_function(
    request: FunctionCreate,
    _: User = Depends(get_current_user),
) -> FunctionInDB:

    function = await create_function(request)
    return function
