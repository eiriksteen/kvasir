from synesis_api.client import MainServerClient
from synesis_schemas.project_server import RunDataSourceAnalysisAgentRequest, RunDataIntegrationAgentRequest, RunPipelineRequest, RunModelIntegrationAgentRequest, RunAnalysisRequest


async def post_run_data_source_analysis(client: MainServerClient, request: RunDataSourceAnalysisAgentRequest) -> None:
    await client.send_request("post", "/agents/run-data-source-analysis-agent", json=request.model_dump(mode="json"))


async def post_run_data_integration(client: MainServerClient, request: RunDataIntegrationAgentRequest) -> None:
    await client.send_request("post", "/agents/run-data-integration-agent", json=request.model_dump(mode="json"))


async def post_run_pipeline_agent(client: MainServerClient, request: RunPipelineRequest) -> None:
    await client.send_request("post", "/agents/run-pipeline-agent", json=request.model_dump(mode="json"))


async def post_run_model_integration(client: MainServerClient, request: RunModelIntegrationAgentRequest) -> None:
    await client.send_request("post", "/agents/run-model-integration-agent", json=request.model_dump(mode="json"))


async def post_run_analysis(client: MainServerClient, request: RunAnalysisRequest) -> None:
    await client.send_request("post", "/agents/run-analysis", json=request.model_dump(mode="json"))
