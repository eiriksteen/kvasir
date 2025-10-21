import uuid
from typing import List


from project_server.client import ProjectClient
from synesis_schemas.main_server import (
    AnalysisObject,
    AnalysisObjectList,
    AnalysisResult,
    AnalysisResultUpdate,
    NotebookSection,
    NotebookSectionCreate,
    NotebookSectionUpdate,
    MoveRequest,
    AggregationObjectWithRawData
)


async def get_analysis_objects_by_project_request(client: ProjectClient, project_id: uuid.UUID) -> AnalysisObjectList:
    response = await client.send_request("get", f"/analysis/analysis-objects/project/{project_id}")
    return AnalysisObjectList(**response.body)


async def get_analysis_object_request(client: ProjectClient, analysis_object_id: uuid.UUID) -> AnalysisObject:
    response = await client.send_request("get", f"/analysis/analysis-object/{analysis_object_id}")
    return AnalysisObject(**response.body)


async def create_section_request(client: ProjectClient, analysis_object_id: uuid.UUID, section_create: NotebookSectionCreate) -> NotebookSection:
    response = await client.send_request("post", f"/analysis/analysis-object/{analysis_object_id}/create-section", json=section_create.model_dump(mode="json"))
    return NotebookSection(**response.body)


async def update_section_request(client: ProjectClient, analysis_object_id: uuid.UUID, section_id: uuid.UUID, section_update: NotebookSectionUpdate) -> NotebookSection:
    response = await client.send_request("patch", f"/analysis/analysis-object/{analysis_object_id}/section/{section_id}", json=section_update.model_dump(mode="json"))
    return NotebookSection(**response.body)


async def delete_section_request(client: ProjectClient, analysis_object_id: uuid.UUID, section_id: uuid.UUID) -> None:
    await client.send_request("delete", f"/analysis/analysis-object/{analysis_object_id}/section/{section_id}")


async def add_analysis_result_to_section_request(client: ProjectClient, analysis_object_id: uuid.UUID, section_id: uuid.UUID, analysis_result_id: uuid.UUID) -> NotebookSection:
    response = await client.send_request("post", f"/analysis/analysis-object/{analysis_object_id}/section/{section_id}/add-analysis-result/{analysis_result_id}")
    return NotebookSection(**response.body)


async def get_data_for_analysis_result_request(client: ProjectClient, analysis_object_id: uuid.UUID, analysis_result_id: uuid.UUID) -> AggregationObjectWithRawData:
    response = await client.send_request("post", f"/analysis/analysis-object/{analysis_object_id}/analysis-result/{analysis_result_id}/get-data")
    return AggregationObjectWithRawData(**response.body)


async def move_element_request(client: ProjectClient, analysis_object_id: uuid.UUID, move_request: MoveRequest) -> None:
    await client.send_request("patch", f"/analysis/analysis-object/{analysis_object_id}/move-element", json=move_request.model_dump(mode="json"))


async def update_analysis_result_request(client: ProjectClient, analysis_result: AnalysisResult) -> AnalysisResult:
    response = await client.send_request("patch", f"/analysis/analysis-result/{analysis_result.id}", json=analysis_result.model_dump(mode="json"))
    return AnalysisResult(**response.body)


async def delete_analysis_result_request(client: ProjectClient, analysis_object_id: uuid.UUID, analysis_result_id: uuid.UUID) -> None:
    await client.send_request("delete", f"/analysis/analysis-object/{analysis_object_id}/analysis-result/{analysis_result_id}")


async def create_analysis_result_request(client: ProjectClient, analysis_result: AnalysisResult) -> AnalysisResult:
    response = await client.send_request("post", "/analysis/analysis-result", json=analysis_result.model_dump(mode="json"))
    return AnalysisResult(**response.body)


async def get_analysis_result_by_id_request(client: ProjectClient, analysis_result_id: uuid.UUID) -> AnalysisResult:
    response = await client.send_request("get", f"/analysis/analysis-result/{analysis_result_id}")
    return AnalysisResult(**response.body)


async def get_analysis_results_by_ids_request(client: ProjectClient, analysis_result_ids: List[uuid.UUID]) -> List[AnalysisResult]:
    response = await client.send_request("post", "/analysis/analysis-results/by-ids", json={"analysis_result_ids": [str(id) for id in analysis_result_ids]})
    return [AnalysisResult(**result) for result in response.body]
