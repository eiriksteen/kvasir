from typing import Annotated
from fastapi import APIRouter, Depends

from synesis_schemas.main_server import (
    ResultChartInDB,
    ResultChartCreate,
    User
)
from synesis_api.modules.analysis.service import create_result_chart
from synesis_api.auth.service import get_current_user

router = APIRouter()


# TODO: Add security checks to verify user owns the analysis result

@router.post("/result-chart", response_model=ResultChartInDB)
async def create_result_chart_endpoint(
    chart_create: ResultChartCreate,
    user: Annotated[User, Depends(get_current_user)] = None
) -> ResultChartInDB:
    """
    Create a new result chart record.
    The chart_script_path should point to a Python script in the project container.
    Use project server endpoints to execute the script and get the ECharts config.
    """
    return await create_result_chart(chart_create)

