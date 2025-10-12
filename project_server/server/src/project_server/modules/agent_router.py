from fastapi import APIRouter, Depends
from typing import Annotated

from synesis_schemas.project_server import (
    RunDataSourceAnalysisAgentRequest,
    RunDataIntegrationAgentRequest,
    RunPipelineAgentRequest,
    RunModelIntegrationAgentRequest
)
from project_server.auth import TokenData, decode_token
from project_server.agents.data_integration.runner import run_data_integration_task
from project_server.agents.data_source_analysis.runner import run_data_source_analysis_task
from project_server.agents.pipeline.runner import run_pipeline_agent_task
from project_server.agents.model_integration.runner import run_model_integration_task


router = APIRouter()


@router.post("/run-data-source-analysis-agent")
async def run_data_source_analysis(
        request: RunDataSourceAnalysisAgentRequest,
        token_data: Annotated[TokenData, Depends(decode_token)] = None):

    await run_data_source_analysis_task.kiq(
        user_id=token_data.user_id,
        source_id=request.data_source_id,
        file_path=request.file_path,
        bearer_token=token_data.bearer_token
    )


@router.post("/run-data-integration-agent")
async def run_data_integration(
        request: RunDataIntegrationAgentRequest,
        token_data: Annotated[TokenData, Depends(decode_token)] = None):

    await run_data_integration_task.kiq(
        user_id=token_data.user_id,
        project_id=request.project_id,
        conversation_id=request.conversation_id,
        run_id=request.run_id,
        data_source_ids=request.data_source_ids,
        prompt_content=request.prompt_content,
        bearer_token=token_data.bearer_token
    )


@router.post("/run-pipeline-agent")
async def run_pipeline(
        request: RunPipelineAgentRequest,
        token_data: Annotated[TokenData, Depends(decode_token)] = None):

    await run_pipeline_agent_task.kiq(
        user_id=token_data.user_id,
        project_id=request.project_id,
        conversation_id=request.conversation_id,
        run_id=request.run_id,
        prompt_content=request.prompt_content,
        bearer_token=token_data.bearer_token,
        input_dataset_ids=request.input_dataset_ids,
        input_model_entity_ids=request.input_model_entity_ids
    )


@router.post("/run-model-integration-agent")
async def run_model_integration(
        request: RunModelIntegrationAgentRequest,
        token_data: Annotated[TokenData, Depends(decode_token)] = None):

    await run_model_integration_task.kiq(
        user_id=token_data.user_id,
        project_id=request.project_id,
        conversation_id=request.conversation_id,
        run_id=request.run_id,
        prompt_content=request.prompt_content,
        bearer_token=token_data.bearer_token,
        public=request.public,
    )
