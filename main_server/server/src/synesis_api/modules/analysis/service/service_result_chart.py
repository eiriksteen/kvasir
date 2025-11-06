import uuid
from typing import List
from sqlalchemy import select, insert, delete
from fastapi import HTTPException

from synesis_api.database.service import execute, fetch_one, fetch_all
from synesis_api.modules.analysis.models import result_chart
from synesis_schemas.main_server import ResultChartInDB, ResultChartCreate


async def create_result_chart(chart_create: ResultChartCreate) -> ResultChartInDB:
    """Create a new result chart record."""
    chart_id = uuid.uuid4()
    chart_in_db = ResultChartInDB(
        id=chart_id,
        **chart_create.model_dump()
    )
    await execute(
        insert(result_chart).values(**chart_in_db.model_dump()),
        commit_after=True
    )
    
    result = await get_result_chart_by_id(chart_id)
    if result is None:
        raise HTTPException(status_code=500, detail="Failed to create result chart")
    return result


async def get_result_chart_by_id(chart_id: uuid.UUID) -> ResultChartInDB | None:
    """Get a result chart by ID."""
    result = await fetch_one(
        select(result_chart).where(result_chart.c.id == chart_id)
    )
    
    if result is None:
        return None
    
    return ResultChartInDB(**result)


async def get_result_charts_by_analysis_result_id(analysis_result_id: uuid.UUID) -> List[ResultChartInDB]:
    """Get all result charts for a specific analysis result."""
    results = await fetch_all(
        select(result_chart).where(
            result_chart.c.analysis_result_id == analysis_result_id)
    )
    
    return [ResultChartInDB(**result) for result in results]


async def delete_result_chart(chart_id: uuid.UUID) -> bool:
    """Delete a result chart by ID."""
    # Check if chart exists
    existing_chart = await get_result_chart_by_id(chart_id)
    if existing_chart is None:
        return False
    
    # Delete the chart record
    await execute(
        delete(result_chart).where(result_chart.c.id == chart_id),
        commit_after=True
    )
    
    return True

