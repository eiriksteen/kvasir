from typing import List
from uuid import UUID

from project_server.client import ProjectClient
from synesis_schemas.main_server import (
    PipelineImplementationCreate,
    Pipeline,
    PipelineInDB,
    PipelineOutputModelEntityInDB,
    PipelineOutputDatasetInDB,
    PipelineRunInDB,
    PipelineRunStatusUpdate,
    PipelineRunDatasetOutputCreate,
    PipelineRunModelEntityOutputCreate,
    PipelineCreate,
    PipelineImplementationInDB
)


async def get_user_pipelines(client: ProjectClient) -> List[PipelineInDB]:
    """Get all pipelines for the current user"""
    response = await client.send_request("get", "/pipeline/user-pipelines")
    return [PipelineInDB(**pipeline) for pipeline in response.body]


async def get_user_pipeline(client: ProjectClient, pipeline_id: str) -> Pipeline:
    """Get a specific pipeline with functions"""
    response = await client.send_request("get", f"/pipeline/pipelines/{pipeline_id}")
    return Pipeline(**response.body)


async def post_pipeline_run_object(client: ProjectClient, pipeline_id: str) -> PipelineRunInDB:
    """Run a pipeline"""
    response = await client.send_request("post", f"/pipeline/pipelines/{pipeline_id}/run-object")
    return PipelineRunInDB(**response.body)


async def patch_pipeline_run_status(client: ProjectClient, pipeline_run_id: UUID, request: PipelineRunStatusUpdate) -> PipelineRunInDB:
    """Update the status of a pipeline run"""
    response = await client.send_request("patch", f"/pipeline/pipelines/{pipeline_run_id}/status", json=request.model_dump(mode="json"))
    return PipelineRunInDB(**response.body)


async def post_pipeline(client: ProjectClient, pipeline_data: PipelineCreate) -> PipelineInDB:
    """Create a new pipeline"""
    response = await client.send_request("post", "/pipeline/pipeline", json=pipeline_data.model_dump(mode="json"))
    return PipelineInDB(**response.body)


async def post_pipeline_implementation(client: ProjectClient, pipeline_implementation_data: PipelineImplementationCreate) -> PipelineImplementationInDB:
    """Create a new pipeline implementation"""
    response = await client.send_request("post", "/pipeline/pipeline-implementation", json=pipeline_implementation_data.model_dump(mode="json"))
    return PipelineImplementationInDB(**response.body)


async def post_pipeline_output_model_entity(client: ProjectClient, pipeline_id: str, request: PipelineRunModelEntityOutputCreate) -> PipelineOutputModelEntityInDB:
    """Output a model entity to a pipeline"""
    response = await client.send_request("post", f"/pipeline/pipelines/{pipeline_id}/output-model-entity", json=request.model_dump(mode="json"))
    return PipelineOutputModelEntityInDB(**response.body)


async def post_pipeline_output_dataset(client: ProjectClient, pipeline_id: str, request: PipelineRunDatasetOutputCreate) -> PipelineOutputDatasetInDB:
    """Output a dataset to a pipeline"""
    response = await client.send_request("post", f"/pipeline/pipelines/{pipeline_id}/output-dataset", json=request.model_dump(mode="json"))
    return PipelineOutputDatasetInDB(**response.body)
