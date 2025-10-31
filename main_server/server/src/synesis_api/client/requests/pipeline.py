from synesis_api.client import MainServerClient
from synesis_schemas.main_server import RunPipelineRequest


async def post_run_pipeline(client: MainServerClient, request: RunPipelineRequest) -> None:
    await client.send_request("post", "/pipeline/run-pipeline", json=request.model_dump(mode="json"))
