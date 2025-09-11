from fastapi import APIRouter, Depends
from typing import Annotated

from synesis_schemas.project_server import RunDataSourceAnalysisRequest, RunDataIntegrationRequest, RunPipelineRequest
from project_server.auth import TokenData, decode_token
from project_server.agents.data_integration.runner import run_data_integration_task
from project_server.agents.data_source_analysis.runner import run_data_source_analysis_task
from project_server.agents.pipeline.runner import run_pipeline_task


router = APIRouter()


@router.post("/run-data-source-analysis")
async def run_data_source_analysis(
        request: RunDataSourceAnalysisRequest,
        token_data: Annotated[TokenData, Depends(decode_token)] = None):

    await run_data_source_analysis_task.kiq(
        user_id=token_data.user_id,
        source_id=request.data_source_id,
        file_path=request.file_path,
        bearer_token=token_data.bearer_token
    )


@router.post("/run-data-integration")
async def run_data_integration(
        request: RunDataIntegrationRequest,
        token_data: Annotated[TokenData, Depends(decode_token)] = None):

    await run_data_integration_task.kiq(
        user_id=token_data.user_id,
        project_id=request.project_id,
        conversation_id=request.conversation_id,
        data_source_ids=request.data_source_ids,
        prompt_content=request.prompt_content,
        bearer_token=token_data.bearer_token
    )


@router.post("/run-pipeline")
async def run_pipeline(
        request: RunPipelineRequest,
        token_data: Annotated[TokenData, Depends(decode_token)] = None):

    await run_pipeline_task.kiq(
        user_id=token_data.user_id,
        project_id=request.project_id,
        conversation_id=request.conversation_id,
        prompt_content=request.prompt_content,
        bearer_token=token_data.bearer_token
    )
