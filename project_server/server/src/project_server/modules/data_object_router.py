from typing import Annotated, Optional
from fastapi import APIRouter, Depends, HTTPException
from uuid import UUID
from datetime import datetime

from project_server.auth import TokenData, decode_token
from synesis_schemas.main_server import TimeSeriesWithRawData

router = APIRouter()


@router.get("/time-series-data/{time_series_id}", response_model=TimeSeriesWithRawData)
async def get_time_series_data(
    time_series_id: UUID,
    start_date: Optional[datetime] = None,
    end_date: datetime = datetime.now(),
    token_data: Annotated[TokenData, Depends(decode_token)] = None
) -> TimeSeriesWithRawData:

    raise HTTPException(status_code=501, detail="Not implemented")


@router.get("/aggregation-object-data/{analysis_id}/{analysis_result_id}", response_model=None, response_model_by_alias=False)
async def get_aggregation_object_by_analysis_result_id(
    analysis_id: UUID,
    analysis_result_id: UUID,
    token_data: Annotated[TokenData, Depends(decode_token)] = None
) -> None:

    raise HTTPException(status_code=501, detail="Not implemented")
