from typing import List
from uuid import UUID

from project_server.client import ProjectClient
from synesis_schemas.main_server import (
    PipelineImplementationCreate,
    Pipeline,
    PipelineInDB,
    PipelineRunInDB,
    PipelineRunStatusUpdate,
    PipelineCreate,
    PipelineImplementationInDB,
    GetPipelinesByIDsRequest,
    PipelineRunCreate
)


async def get_pipeline_runs(client: ProjectClient) -> List[PipelineRunInDB]:
    """Get all pipeline runs for the current user"""
    response = await client.send_request("get", "/pipeline/pipelines/runs")
    return [PipelineRunInDB(**run) for run in response.body]


async def get_pipeline(client: ProjectClient, pipeline_id: UUID) -> Pipeline:
    """Get a pipeline by ID"""
    response = await client.send_request("get", f"/pipeline/pipelines/{pipeline_id}")
    return Pipeline(**response.body)


async def get_pipelines_by_ids(client: ProjectClient, request: GetPipelinesByIDsRequest) -> List[Pipeline]:
    """Get pipelines by IDs"""
    response = await client.send_request("get", "/pipeline/pipelines-by-ids", json=request.model_dump(mode="json"))
    return [Pipeline(**pipeline) for pipeline in response.body]


async def post_pipeline(client: ProjectClient, pipeline_data: PipelineCreate) -> PipelineInDB:
    """Create a new pipeline"""
    response = await client.send_request("post", "/pipeline/pipeline", json=pipeline_data.model_dump(mode="json"))
    return PipelineInDB(**response.body)


async def post_pipeline_implementation(client: ProjectClient, pipeline_implementation_data: PipelineImplementationCreate) -> PipelineImplementationInDB:
    """Create a new pipeline implementation"""
    response = await client.send_request("post", "/pipeline/pipeline-implementation", json=pipeline_implementation_data.model_dump(mode="json"))
    return PipelineImplementationInDB(**response.body)


async def post_pipeline_run(client: ProjectClient, request: PipelineRunCreate) -> PipelineRunInDB:
    """Create a new pipeline run"""
    response = await client.send_request("post", "/pipeline/pipeline-run", json=request.model_dump(mode="json"))
    return PipelineRunInDB(**response.body)


async def patch_pipeline_run_status(client: ProjectClient, pipeline_run_id: UUID, request: PipelineRunStatusUpdate) -> PipelineRunInDB:
    """Update the status of a pipeline run"""
    response = await client.send_request("patch", f"/pipeline/pipelines/{pipeline_run_id}/status", json=request.model_dump(mode="json"))
    return PipelineRunInDB(**response.body)
