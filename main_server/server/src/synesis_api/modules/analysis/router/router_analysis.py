import uuid
import time
import redis
from typing import Annotated, List
from fastapi import APIRouter, Depends, HTTPException
from fastapi.responses import FileResponse, StreamingResponse, Response
from pathlib import Path
from starlette.background import BackgroundTask
import aiofiles
# from weasyprint import HTML


from synesis_schemas.main_server import (
    AnalysisObject, 
    AnalysisObjectCreate, 
    AnalysisObjectList, 
    AnalysisStatusMessage,
    NotebookSection,
    NotebookSectionCreate,
    NotebookSectionUpdate,
    AnalysisResultUpdate,
    AnalysisObjectSmall,
    AnalysisResult,
    GenerateReportRequest,
    MoveRequest,
    AnalysisResultFindRequest,
    User,
    AggregationObjectWithRawData,
)
from synesis_api.auth.service import get_current_user, user_owns_runs
from synesis_api.modules.analysis.service import (
    create_analysis_object,
    get_analysis_object_by_id,
    get_analysis_objects_small_by_project_id,
    delete_analysis_object,
    check_user_owns_analysis_object,
    delete_notebook_section_recursive,
    create_section,
    update_section,
    update_analysis_result,
    add_analysis_result_to_section,
    generate_notebook_report,
    get_notebook_by_id,
    move_element as move_element_service,
    delete_analysis_result as delete_analysis_result_service,
    get_analysis_results_by_ids,
    get_analysis_result_by_id,
    create_analysis_result
)
from synesis_api.modules.data_objects.service import get_aggregation_object_by_analysis_result_id
from synesis_api.modules.node.service import get_node_by_analysis_object_id
from synesis_api.redis import get_redis
from synesis_api.utils.markdown_utils import convert_markdown_to_html
from synesis_api.client import MainServerClient, get_aggregation_object_payload_data_by_analysis_result_id
from synesis_api.auth.service import oauth2_scheme

router = APIRouter()

SSE_MAX_TIMEOUT = 3600


@router.post("/analysis-object", response_model=AnalysisObjectSmall)
async def post_analysis_object(
    analysis_object_create: AnalysisObjectCreate,
    user: Annotated[User, Depends(get_current_user)] = None
) -> AnalysisObjectSmall:
    return await create_analysis_object(analysis_object_create, user.id)



@router.get("/analysis-objects/project/{project_id}", response_model=AnalysisObjectList)
async def get_analysis_objects_by_project(
    project_id: uuid.UUID,
    user: Annotated[User, Depends(get_current_user)] = None
) -> AnalysisObjectList:
    return await get_analysis_objects_small_by_project_id(project_id)


@router.get("/analysis-object/{analysis_object_id}", response_model=AnalysisObject)
async def get_analysis_object(
    analysis_object_id: uuid.UUID,
    user: Annotated[User, Depends(get_current_user)] = None
) -> AnalysisObject:
    if not await check_user_owns_analysis_object(user.id, analysis_object_id):
        raise HTTPException(
            status_code=403, 
            detail="You do not have permission to access this analysis object"
        )
    return await get_analysis_object_by_id(analysis_object_id)



@router.delete("/analysis-object/{analysis_object_id}", response_model=uuid.UUID)
async def delete_analysis_object_endpoint(
    analysis_object_id: uuid.UUID,
    user: Annotated[User, Depends(get_current_user)] = None
) -> uuid.UUID:
    if not await check_user_owns_analysis_object(user.id, analysis_object_id):
        raise HTTPException(
            status_code=403, 
            detail="You do not have permission to delete this analysis object"
        )
    
    node_id = await get_node_by_analysis_object_id(analysis_object_id)
    return await delete_analysis_object(analysis_object_id, node_id, user.id)



@router.post("/analysis-object/{analysis_object_id}/generate-report", response_class=FileResponse)
async def generate_report_endpoint(
    analysis_object_id: uuid.UUID,
    generate_report_request: GenerateReportRequest,
    user: Annotated[User, Depends(get_current_user)] = None
) -> FileResponse:
    if not await check_user_owns_analysis_object(user.id, analysis_object_id):
        raise HTTPException(
            status_code=403, 
            detail="You do not have permission to modify this analysis object"
        )
    
    analysis_object = await get_analysis_object_by_id(analysis_object_id)
    notebook = await get_notebook_by_id(analysis_object.notebook_id)
    
    # Generate markdown report content
    report_content = await generate_notebook_report(analysis_object, notebook, generate_report_request.include_code, user.id)
    
    # Convert markdown to HTML
    html_content = convert_markdown_to_html(report_content)
    
    # Create temporary HTML file
    html_path = Path.cwd() / "tmp" / f"{generate_report_request.filename}_temp.html"
    async with aiofiles.open(html_path, mode="w", encoding="utf-8") as f:
        await f.write(html_content)
    
    # Convert HTML to PDF using weasyprint
    pdf_path = Path.cwd() / "tmp" / f"{generate_report_request.filename}.pdf"
    
    # TODO: FIX THIS
    
    # try:
        
    #     # Convert HTML to PDF
    #     HTML(string=html_content).write_pdf(str(pdf_path))
        
    #     # Clean up temporary HTML file
    #     html_path.unlink()
        
    #     return FileResponse(
    #         path=pdf_path,
    #         filename=f"{generate_report_request.filename}.pdf",
    #         media_type="application/pdf",
    #         background=BackgroundTask(pdf_path.unlink)
    #     )
    # except Exception as e:
    #     # Clean up files on error
    #     if html_path.exists():
    #         html_path.unlink()
    #     if pdf_path.exists():
    #         pdf_path.unlink()
    #     raise HTTPException(
    #         status_code=500,
    #         detail=f"Failed to generate PDF: {str(e)}"
    #     )


@router.get("/analysis-agent-sse/{run_id}")
async def analysis_agent_sse(
    run_id: uuid.UUID,
    cache: Annotated[redis.Redis, Depends(get_redis)],
    timeout: int = SSE_MAX_TIMEOUT,
    user: Annotated[User, Depends(get_current_user)] = None
) -> StreamingResponse:
    """Stream analysis status messages for a running run."""
    if not user or not await user_owns_runs(user.id, [run_id]):
        raise HTTPException(
            status_code=403, detail="You do not have permission to access this run")

    timeout = min(timeout, SSE_MAX_TIMEOUT)

    async def stream_run_updates():
        response = await cache.xread({str(run_id) + "-result": "$"}, count=1, block=timeout*1000)

        start_time = time.time()
        last_id = response[0][1][-1][0] if response else None
        data = response[0][1][0][1]

        if 'result' in data.keys():
            analysis_result = AnalysisResult.model_validate_json(data["result"])
            data["result"] = analysis_result
            status_message = AnalysisStatusMessage.model_validate(data)
        
            yield f"data: {status_message.model_dump_json(by_alias=True)}\n\n"

        while True:
            response = await cache.xread({str(run_id) + "-result": last_id}, count=1)

            if response:
                start_time = time.time()
                last_id = response[0][1][-1][0]
                data = response[0][1][0][1]
                if "result" in data.keys():
                    analysis_result = AnalysisResult.model_validate_json(data["result"])
                    data["result"] = analysis_result
                    status_message = AnalysisStatusMessage.model_validate(data)
                    yield f"data: {status_message.model_dump_json(by_alias=True)}\n\n"


            if start_time + timeout < time.time():
                break

    return StreamingResponse(stream_run_updates(), media_type="text/event-stream")
    
@router.post("/analysis-object/{analysis_object_id}/create-section", response_model=NotebookSection)
async def create_section_endpoint(
    analysis_object_id: uuid.UUID,
    section_create: NotebookSectionCreate,
    user: Annotated[User, Depends(get_current_user)] = None,
) -> NotebookSection:
    if not await check_user_owns_analysis_object(user.id, analysis_object_id):
        raise HTTPException(
            status_code=403, 
            detail="You do not have permission to access this analysis object"
        )
    
    return await create_section(section_create)

@router.patch("/analysis-object/{analysis_object_id}/section/{section_id}", response_model=NotebookSection)
async def update_section_endpoint(
    analysis_object_id: uuid.UUID,
    section_id: uuid.UUID,
    section_update: NotebookSectionUpdate,
    user: Annotated[User, Depends(get_current_user)] = None,
) -> NotebookSection:
    if not await check_user_owns_analysis_object(user.id, analysis_object_id):
        raise HTTPException(
            status_code=403, 
            detail="You do not have permission to access this analysis object"  
        )
    
    return await update_section(section_id, section_update)

@router.delete("/analysis-object/{analysis_object_id}/section/{section_id}")
async def delete_section_endpoint(
    analysis_object_id: uuid.UUID,
    section_id: uuid.UUID,
    user: Annotated[User, Depends(get_current_user)] = None,
):
    if not await check_user_owns_analysis_object(user.id, analysis_object_id):
        raise HTTPException(
            status_code=403, 
            detail="You do not have permission to access this analysis object"  
        )
    
    await delete_notebook_section_recursive(section_id)
    return

@router.post("/analysis-object/{analysis_object_id}/section/{section_id}/add-analysis-result/{analysis_result_id}", response_model=NotebookSection)
async def add_analysis_result_to_section_endpoint(
    analysis_object_id: uuid.UUID,
    section_id: uuid.UUID,
    analysis_result_id: uuid.UUID,
    user: Annotated[User, Depends(get_current_user)] = None,
) -> NotebookSection:
    if not await check_user_owns_analysis_object(user.id, analysis_object_id):
        raise HTTPException(
            status_code=403, 
            detail="You do not have permission to access this analysis object"  
        )
    
    return await add_analysis_result_to_section(section_id, analysis_result_id)


@router.get("/analysis-object/{analysis_object_id}/analysis-result/{analysis_result_id}/get-data", response_model=AggregationObjectWithRawData)
async def get_data_for_analysis_result(
    analysis_object_id: uuid.UUID,
    analysis_result_id: uuid.UUID,
    user: Annotated[User, Depends(get_current_user)] = None,
    token: str = Depends(oauth2_scheme)
) -> AggregationObjectWithRawData:
    if not await check_user_owns_analysis_object(user.id, analysis_object_id):
        raise HTTPException(
            status_code=403, 
            detail="You do not have permission to access this analysis object"  
        )

    client = MainServerClient(token)
    result = await get_aggregation_object_payload_data_by_analysis_result_id(client, analysis_object_id, analysis_result_id)
    aggregation_object_in_db = await get_aggregation_object_by_analysis_result_id(analysis_result_id)
    aggregation_object_with_raw_data = AggregationObjectWithRawData(**aggregation_object_in_db.model_dump(), data=result)
    return aggregation_object_with_raw_data

@router.patch("/analysis-object/{analysis_object_id}/move-element")
async def move_element(
    analysis_object_id: uuid.UUID,
    move_request: MoveRequest,
    user: Annotated[User, Depends(get_current_user)] = None,
):
    if not await check_user_owns_analysis_object(user.id, analysis_object_id):
        raise HTTPException(
            status_code=403, 
            detail="You do not have permission to access this analysis object"  
        )
    await move_element_service(move_request)
    return


@router.patch("/analysis-result/{analysis_result_id}", response_model=AnalysisResult)
async def update_analysis_result_endpoint(
    analysis_result: AnalysisResult,
    user: Annotated[User, Depends(get_current_user)] = None,
) -> AnalysisResult:
    
    return await update_analysis_result(analysis_result)

@router.delete("/analysis-object/{analysis_object_id}/analysis-result/{analysis_result_id}")
async def delete_analysis_result_endpoint(
    analysis_object_id: uuid.UUID,
    analysis_result_id: uuid.UUID,
    user: Annotated[User, Depends(get_current_user)] = None,
):
    if not await check_user_owns_analysis_object(user.id, analysis_object_id):
        raise HTTPException(
            status_code=403, 
            detail="You do not have permission to access this analysis object"  
        )
    await delete_analysis_result_service(analysis_result_id)
    return


@router.post("/analysis-result", response_model=AnalysisResult)
async def create_analysis_result_endpoint(
    analysis_result: AnalysisResult,
    user: Annotated[User, Depends(get_current_user)] = None,
) -> AnalysisResult:
    return await create_analysis_result(analysis_result)



@router.get("/analysis-result/{analysis_result_id}", response_model=AnalysisResult)
async def get_analysis_result_endpoint(
    analysis_result_id: uuid.UUID,
    user: Annotated[User, Depends(get_current_user)] = None,
) -> AnalysisResult:
    result = await get_analysis_result_by_id(analysis_result_id)
    if result is None:
        raise HTTPException(status_code=404, detail="Analysis result not found")
    return result


@router.post("/analysis-results/by-ids", response_model=List[AnalysisResult])
async def get_analysis_results_by_ids_endpoint(
    analysis_result_find_request: AnalysisResultFindRequest,
    user: Annotated[User, Depends(get_current_user)] = None,
) -> List[AnalysisResult]:
    return await get_analysis_results_by_ids(analysis_result_find_request.analysis_result_ids)