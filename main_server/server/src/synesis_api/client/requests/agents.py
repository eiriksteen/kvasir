from synesis_api.client import MainServerClient
from synesis_schemas.project_server import RunDataSourceAnalysisRequest, RunDataIntegrationRequest, RunPipelineRequest, RunModelIntegrationRequest, RunAnalysisRequest


async def post_run_data_source_analysis(client: MainServerClient, request: RunDataSourceAnalysisRequest) -> None:
    await client.send_request("post", "/agents/run-data-source-analysis", json=request.model_dump(mode="json"))


async def post_run_data_integration(client: MainServerClient, request: RunDataIntegrationRequest) -> None:
    await client.send_request("post", "/agents/run-data-integration", json=request.model_dump(mode="json"))


async def post_run_pipeline(client: MainServerClient, request: RunPipelineRequest) -> None:
    await client.send_request("post", "/agents/run-pipeline", json=request.model_dump(mode="json"))


async def post_run_model_integration(client: MainServerClient, request: RunModelIntegrationRequest) -> None:
    await client.send_request("post", "/agents/run-model-integration", json=request.model_dump(mode="json"))


async def post_run_analysis(client: MainServerClient, request: RunAnalysisRequest) -> None:
    await client.send_request("post", "/agents/run-analysis", json=request.model_dump(mode="json"))