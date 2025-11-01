from fastapi import APIRouter, Depends, HTTPException
from typing import Annotated
import uuid
from fastapi.responses import FileResponse

from project_server.auth import TokenData, decode_token


router = APIRouter()


@router.get("/analysis-object/{analysis_id}/analysis-result/{analysis_result_id}/{url}", response_class=FileResponse)
async def get_plots_for_analysis_result(
    analysis_id: uuid.UUID,
    analysis_result_id: uuid.UUID,
    url: str,
    token_data: Annotated[TokenData, Depends(decode_token)] = None
) -> FileResponse:
    return HTTPException(status_code=501, detail="Function not implemented - needs to be fixed")
    # analysis_output_path = ANALYSIS_DIR / \
    #     str(analysis_id) / str(analysis_result_id) / "plots"
    # analysis_output_filepath = analysis_output_path / url

    # if not analysis_output_filepath.exists():
    #     raise HTTPException(status_code=404, detail="Plot not found")

    # return FileResponse(path=analysis_output_filepath, media_type="image/png")
