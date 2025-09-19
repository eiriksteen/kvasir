from typing import List

from project_server.client import ProjectClient
from synesis_schemas.main_server import PipelineCreate, PipelineFull, PipelineInDB


async def get_user_pipelines(client: ProjectClient) -> List[PipelineInDB]:
    """Get all pipelines for the current user"""
    response = await client.send_request("get", "/pipeline/user-pipelines")
    return [PipelineInDB(**pipeline) for pipeline in response.body]


async def get_user_pipeline(client: ProjectClient, pipeline_id: str) -> PipelineFull:
    """Get a specific pipeline with functions"""
    response = await client.send_request("get", f"/pipeline/user-pipeline/{pipeline_id}")
    return PipelineFull(**response.body)


async def post_pipeline(client: ProjectClient, pipeline_data: PipelineCreate) -> PipelineInDB:
    """Create a new pipeline"""
    response = await client.send_request("post", "/pipeline/pipeline", json=pipeline_data.model_dump(mode="json"))
    return PipelineInDB(**response.body)
