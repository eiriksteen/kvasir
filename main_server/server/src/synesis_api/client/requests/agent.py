from synesis_api.client import MainServerClient
from synesis_schemas.project_server import RunSWERequest, RunAnalysisRequest


async def post_run_swe(client: MainServerClient, request: RunSWERequest) -> None:
    await client.send_request("post", "/agents/run-swe", json=request.model_dump(mode="json"))


async def post_run_analysis(client: MainServerClient, request: RunAnalysisRequest) -> None:
    await client.send_request("post", "/agents/run-analysis", json=request.model_dump(mode="json"))
