from typing import Annotated
from fastapi import APIRouter, Depends

from synesis_schemas.main_server import (
    ResultTableInDB,
    ResultTableCreate,
    User
)
from synesis_api.modules.analysis.service import create_result_table
from synesis_api.auth.service import get_current_user

router = APIRouter()


# TODO: Add security checks to verify user owns the analysis result

@router.post("/result-table", response_model=ResultTableInDB)
async def create_result_table_endpoint(
    table_create: ResultTableCreate,
    user: Annotated[User, Depends(get_current_user)] = None
) -> ResultTableInDB:
    """
    Create a new result table record.
    The table_path should point to a parquet file in the project container.
    Use project server endpoints to read and render the table data.
    """
    return await create_result_table(table_create)

