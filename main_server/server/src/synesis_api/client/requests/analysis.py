import uuid
from fastapi.responses import Response

from synesis_api.client import MainServerClient


async def get_plots_for_analysis_result_request(client: MainServerClient, analysis_id: uuid.UUID, analysis_result_id: uuid.UUID, plot_url: str) -> Response:
    response = await client.send_request("get", f"/analysis/analysis-object/{analysis_id}/analysis-result/{analysis_result_id}/{plot_url}")

    # The response.body contains the image bytes from the project_server
    return Response(
        content=response.body,
        media_type=response.content_type
    )
