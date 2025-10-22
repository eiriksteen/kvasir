from fastapi import APIRouter, Depends
from typing import Annotated

from synesis_schemas.project_server import (
    RunSWERequest,
    RunAnalysisRequest
)
from project_server.auth import TokenData, decode_token
from project_server.agents.analysis.runner import run_analysis_task
from project_server.agents.swe.runner import run_swe_task


router = APIRouter()


@router.post("/run-swe")
async def run_swe(
        request: RunSWERequest,
        token_data: Annotated[TokenData, Depends(decode_token)] = None):

    await run_swe_task.kiq(
        user_id=token_data.user_id,
        swe_request=request,
        bearer_token=token_data.bearer_token
    )


@router.post("/run-analysis")
async def run_analysis(
        request: RunAnalysisRequest,
        token_data: Annotated[TokenData, Depends(decode_token)] = None
):
    await run_analysis_task.kiq(
        user_id=token_data.user_id,
        analysis_request=request,
        bearer_token=token_data.bearer_token
    )
