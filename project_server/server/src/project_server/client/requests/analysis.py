import uuid
from typing import List


from project_server.client import ProjectClient
from synesis_schemas.main_server import (
    Analysis,
    AnalysisSmall,
    AnalysisResult,
    # AnalysisResultUpdate,
    NotebookSection,
    NotebookSectionCreate,
    NotebookSectionUpdate,
    MoveRequest,
    # AggregationObjectWithRawData,
    GetAnalysesByIDsRequest,
    ResultImageInDB,
    ResultImageCreate,
    ResultChartInDB,
    ResultChartCreate,
    ResultTableInDB,
    ResultTableCreate
)


async def get_analyses_by_project_request(client: ProjectClient, project_id: uuid.UUID) -> List[AnalysisSmall]:
    response = await client.send_request("get", f"/project/project-analyses/{project_id}")
    return [AnalysisSmall(**analysis) for analysis in response.body]


async def get_analyses_by_ids(client: ProjectClient, request: GetAnalysesByIDsRequest) -> List[Analysis]:
    response = await client.send_request("get", f"/analysis/analyses-by-ids", json=request.model_dump(mode="json"))
    return [Analysis(**analysis) for analysis in response.body]


async def get_analysis_request(client: ProjectClient, analysis_id: uuid.UUID) -> Analysis:
    response = await client.send_request("get", f"/analysis/analysis-object/{analysis_id}")
    return Analysis(**response.body)


async def create_section_request(client: ProjectClient, analysis_id: uuid.UUID, section_create: NotebookSectionCreate) -> NotebookSection:
    response = await client.send_request("post", f"/analysis/analysis-object/{analysis_id}/create-section", json=section_create.model_dump(mode="json"))
    return NotebookSection(**response.body)


async def update_section_request(client: ProjectClient, analysis_id: uuid.UUID, section_id: uuid.UUID, section_update: NotebookSectionUpdate) -> NotebookSection:
    response = await client.send_request("patch", f"/analysis/analysis-object/{analysis_id}/section/{section_id}", json=section_update.model_dump(mode="json"))
    return NotebookSection(**response.body)


async def delete_section_request(client: ProjectClient, analysis_id: uuid.UUID, section_id: uuid.UUID) -> None:
    await client.send_request("delete", f"/analysis/analysis-object/{analysis_id}/section/{section_id}")


async def add_analysis_result_to_section_request(client: ProjectClient, analysis_id: uuid.UUID, section_id: uuid.UUID, analysis_result_id: uuid.UUID) -> NotebookSection:
    response = await client.send_request("post", f"/analysis/analysis-object/{analysis_id}/section/{section_id}/add-analysis-result/{analysis_result_id}")
    return NotebookSection(**response.body)


async def get_data_for_analysis_result_request(client: ProjectClient, analysis_id: uuid.UUID, analysis_result_id: uuid.UUID) -> None:
    raise NotImplementedError("Function not implemented - needs to be fixed")
    response = await client.send_request("post", f"/analysis/analysis-object/{analysis_id}/analysis-result/{analysis_result_id}/get-data")
    return None


async def move_element_request(client: ProjectClient, analysis_id: uuid.UUID, move_request: MoveRequest) -> None:
    await client.send_request("patch", f"/analysis/analysis-object/{analysis_id}/move-element", json=move_request.model_dump(mode="json"))


async def update_analysis_result_request(client: ProjectClient, analysis_result: AnalysisResult) -> AnalysisResult:
    response = await client.send_request("patch", f"/analysis/analysis-result/{analysis_result.id}", json=analysis_result.model_dump(mode="json"))
    return AnalysisResult(**response.body)


async def delete_analysis_result_request(client: ProjectClient, analysis_id: uuid.UUID, analysis_result_id: uuid.UUID) -> None:
    await client.send_request("delete", f"/analysis/analysis-object/{analysis_id}/analysis-result/{analysis_result_id}")


async def create_analysis_result_request(client: ProjectClient, analysis_result: AnalysisResult) -> AnalysisResult:
    response = await client.send_request("post", "/analysis/analysis-result", json=analysis_result.model_dump(mode="json"))
    return AnalysisResult(**response.body)


async def get_analysis_result_by_id_request(client: ProjectClient, analysis_result_id: uuid.UUID) -> AnalysisResult:
    response = await client.send_request("get", f"/analysis/analysis-result/{analysis_result_id}")
    return AnalysisResult(**response.body)


async def get_analysis_results_by_ids_request(client: ProjectClient, analysis_result_ids: List[uuid.UUID]) -> List[AnalysisResult]:
    response = await client.send_request("post", "/analysis/analysis-results/by-ids", json={"analysis_result_ids": [str(id) for id in analysis_result_ids]})
    return [AnalysisResult(**result) for result in response.body]


async def create_result_image(client: ProjectClient, image_create: ResultImageCreate) -> ResultImageInDB:
    """Create a new result image record in the database."""
    response = await client.send_request(
        "post",
        "/analysis/result-image",
        json=image_create.model_dump(mode="json")
    )
    return ResultImageInDB(**response.body)


async def create_result_chart(client: ProjectClient, chart_create: ResultChartCreate) -> ResultChartInDB:
    """Create a new result chart record in the database."""
    response = await client.send_request(
        "post",
        "/analysis/result-chart",
        json=chart_create.model_dump(mode="json")
    )
    return ResultChartInDB(**response.body)


async def create_result_table(client: ProjectClient, table_create: ResultTableCreate) -> ResultTableInDB:
    """Create a new result table record in the database."""
    response = await client.send_request(
        "post",
        "/analysis/result-table",
        json=table_create.model_dump(mode="json")
    )
    return ResultTableInDB(**response.body)
