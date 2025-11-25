import uuid
import time
import redis
import json
from datetime import datetime, timezone
from typing import Annotated, List, Union
from fastapi import APIRouter, Depends, HTTPException
from fastapi.responses import StreamingResponse
from sqlalchemy import select
from pydantic import BaseModel
# from weasyprint import HTML


from kvasir_api.auth.schema import User
from kvasir_api.auth.service import get_current_user, user_owns_runs, user_owns_analysis
from kvasir_api.modules.analysis.service import (
    get_analysis_service,
)
from kvasir_ontology.entities.analysis.interface import AnalysisInterface
from kvasir_ontology.entities.analysis.data_model import (
    Analysis,
    AnalysisCreate,
    SectionCreate,
    CodeCellCreate,
    MarkdownCellCreate,
    CodeOutputCreate,
    Section,
    AnalysisCell,
)
from kvasir_ontology.visualization.data_model import (
    ImageCreate,
    EchartCreate,
    TableCreate,
)
# from kvasir_api.utils.markdown_utils import convert_markdown_to_html

router = APIRouter()

SSE_MAX_TIMEOUT = 3600


@router.get("/analysis-agent-sse/{run_id}")
async def analysis_agent_sse(
    run_id: uuid.UUID,
    timeout: int = SSE_MAX_TIMEOUT,
    user: Annotated[User, Depends(get_current_user)] = None,
    analysis_service: Annotated[AnalysisInterface,
                                Depends(get_analysis_service)] = None
) -> StreamingResponse:
    """Stream analysis status messages for a running run."""
    if not user or not await user_owns_runs(user.id, [run_id]):
        raise HTTPException(
            status_code=403, detail="You do not have permission to access this run")

    timeout = min(timeout, SSE_MAX_TIMEOUT)

    async def stream_run_updates():
        start_time = time.time()

        async for item in analysis_service.listen_to_analysis_stream(run_id):
            if isinstance(item, (Section, AnalysisCell)):
                yield f"data: {item.model_dump_json(by_alias=True)}\n\n"

            # Check timeout
            if time.time() - start_time > timeout:
                break

    return StreamingResponse(stream_run_updates(), media_type="text/event-stream")


# Routes for AnalysisInterface methods using dependency injection

@router.post("/analysis", response_model=Analysis)
async def create_analysis_endpoint(
    analysis_create: AnalysisCreate,
    _: Annotated[User, Depends(get_current_user)],
    analysis_service: Annotated[AnalysisInterface,
                                Depends(get_analysis_service)]
) -> Analysis:
    return await analysis_service.create_analysis(analysis_create)


@router.get("/analysis/{analysis_id}", response_model=Analysis)
async def get_analysis_endpoint(
    analysis_id: uuid.UUID,
    user: Annotated[User, Depends(get_current_user)],
    analysis_service: Annotated[AnalysisInterface,
                                Depends(get_analysis_service)]
) -> Analysis:
    if not await user_owns_analysis(user.id, analysis_id):
        raise HTTPException(
            status_code=403,
            detail="You do not have permission to access this analysis"
        )
    return await analysis_service.get_analysis(analysis_id)


@router.post("/analyses-by-ids", response_model=List[Analysis])
async def get_analyses_endpoint(
    analysis_ids: List[uuid.UUID],
    _: Annotated[User, Depends(get_current_user)],
    analysis_service: Annotated[AnalysisInterface,
                                Depends(get_analysis_service)]
) -> List[Analysis]:
    return await analysis_service.get_analyses(analysis_ids)


@router.post("/analysis/{analysis_id}/section", response_model=Section)
async def create_section_endpoint(
    analysis_id: uuid.UUID,
    section_create: SectionCreate,
    user: Annotated[User, Depends(get_current_user)],
    analysis_service: Annotated[AnalysisInterface,
                                Depends(get_analysis_service)]
) -> Section:
    if not await user_owns_analysis(user.id, analysis_id):
        raise HTTPException(
            status_code=403,
            detail="You do not have permission to access this analysis"
        )
    section_create.analysis_id = analysis_id
    return await analysis_service.create_section(section_create)


@router.post("/analysis/{analysis_id}/markdown-cell", response_model=AnalysisCell)
async def create_markdown_cell_endpoint(
    analysis_id: uuid.UUID,
    markdown_cell_create: MarkdownCellCreate,
    user: Annotated[User, Depends(get_current_user)],
    analysis_service: Annotated[AnalysisInterface,
                                Depends(get_analysis_service)]
) -> AnalysisCell:
    if not await user_owns_analysis(user.id, analysis_id):
        raise HTTPException(
            status_code=403,
            detail="You do not have permission to access this analysis"
        )
    return await analysis_service.create_markdown_cell(markdown_cell_create)


@router.post("/analysis/{analysis_id}/code-cell", response_model=AnalysisCell)
async def create_code_cell_endpoint(
    analysis_id: uuid.UUID,
    code_cell_create: CodeCellCreate,
    user: Annotated[User, Depends(get_current_user)],
    analysis_service: Annotated[AnalysisInterface,
                                Depends(get_analysis_service)]
) -> AnalysisCell:
    if not await user_owns_analysis(user.id, analysis_id):
        raise HTTPException(
            status_code=403,
            detail="You do not have permission to access this analysis"
        )
    return await analysis_service.create_code_cell(code_cell_create)


@router.post("/analysis/{analysis_id}/code-output", response_model=Analysis)
async def create_code_output_endpoint(
    analysis_id: uuid.UUID,
    code_output_create: CodeOutputCreate,
    user: Annotated[User, Depends(get_current_user)],
    analysis_service: Annotated[AnalysisInterface,
                                Depends(get_analysis_service)]
) -> Analysis:
    if not await user_owns_analysis(user.id, analysis_id):
        raise HTTPException(
            status_code=403,
            detail="You do not have permission to access this analysis"
        )
    return await analysis_service.create_code_output(code_output_create)


@router.post("/analysis/{analysis_id}/code-cell/{code_cell_id}/image", response_model=Analysis)
async def create_code_output_image_endpoint(
    analysis_id: uuid.UUID,
    code_cell_id: uuid.UUID,
    image_create: ImageCreate,
    user: Annotated[User, Depends(get_current_user)],
    analysis_service: Annotated[AnalysisInterface,
                                Depends(get_analysis_service)]
) -> Analysis:
    if not await user_owns_analysis(user.id, analysis_id):
        raise HTTPException(
            status_code=403,
            detail="You do not have permission to access this analysis"
        )
    return await analysis_service.create_code_output_image(code_cell_id, image_create)


@router.post("/analysis/{analysis_id}/code-cell/{code_cell_id}/echart", response_model=Analysis)
async def create_code_output_echart_endpoint(
    analysis_id: uuid.UUID,
    code_cell_id: uuid.UUID,
    echart_create: EchartCreate,
    user: Annotated[User, Depends(get_current_user)],
    analysis_service: Annotated[AnalysisInterface,
                                Depends(get_analysis_service)]
) -> Analysis:
    if not await user_owns_analysis(user.id, analysis_id):
        raise HTTPException(
            status_code=403,
            detail="You do not have permission to access this analysis"
        )
    return await analysis_service.create_code_output_echart(code_cell_id, echart_create)


@router.post("/analysis/{analysis_id}/code-cell/{code_cell_id}/table", response_model=Analysis)
async def create_code_output_table_endpoint(
    analysis_id: uuid.UUID,
    code_cell_id: uuid.UUID,
    table_create: TableCreate,
    user: Annotated[User, Depends(get_current_user)],
    analysis_service: Annotated[AnalysisInterface,
                                Depends(get_analysis_service)]
) -> Analysis:
    if not await user_owns_analysis(user.id, analysis_id):
        raise HTTPException(
            status_code=403,
            detail="You do not have permission to access this analysis"
        )
    return await analysis_service.create_code_output_table(code_cell_id, table_create)


@router.delete("/analysis/{analysis_id}")
async def delete_analysis_endpoint(
    analysis_id: uuid.UUID,
    user: Annotated[User, Depends(get_current_user)],
    analysis_service: Annotated[AnalysisInterface,
                                Depends(get_analysis_service)]
) -> None:
    if not await user_owns_analysis(user.id, analysis_id):
        raise HTTPException(
            status_code=403,
            detail="You do not have permission to access this analysis"
        )
    await analysis_service.delete_analysis(analysis_id)
