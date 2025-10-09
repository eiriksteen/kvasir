import uuid
from typing import List
from project_server.client import ProjectClient
from synesis_schemas.main_server import (
    AnalysisObject,
    AnalysisObjectCreate,
    AnalysisObjectList,
    AnalysisObjectSmall,
    AnalysisResult,
    AnalysisResultUpdate,
    NotebookSection,
    NotebookSectionCreate,
    NotebookSectionUpdate,
    MoveRequest,
    GenerateReportRequest,
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
    response = await client.send_request("put", f"/analysis/analysis-object/{analysis_object_id}/section/{section_id}", json=section_update.model_dump(mode="json"))
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
    await client.send_request("put", f"/analysis/analysis-object/{analysis_object_id}/move-element", json=move_request.model_dump(mode="json"))


async def update_analysis_result_request(client: ProjectClient, analysis_result_id: uuid.UUID, analysis_result_update: AnalysisResultUpdate) -> AnalysisResult:
    response = await client.send_request("put", f"/analysis/analysis-result/{analysis_result_id}", json=analysis_result_update.model_dump(mode="json"))
    return AnalysisResult(**response.body)


async def delete_analysis_result_request(client: ProjectClient, analysis_object_id: uuid.UUID, analysis_result_id: uuid.UUID) -> None:
    await client.send_request("delete", f"/analysis/analysis-object/{analysis_object_id}/analysis-result/{analysis_result_id}")


async def create_analysis_result_request(client: ProjectClient, analysis_result: AnalysisResult) -> AnalysisResult:
    response = await client.send_request("post", "/analysis/analysis-result", json=analysis_result.model_dump(mode="json"))
    return AnalysisResult(**response.body)


async def create_analysis_run_request(client: ProjectClient, analysis_result_id: uuid.UUID, run_id: uuid.UUID) -> None:
    await client.send_request("post", f"/analysis/analysis-result/{analysis_result_id}/run?run_id={run_id}")


async def get_analysis_result_by_id_request(client: ProjectClient, analysis_result_id: uuid.UUID) -> AnalysisResult:
    response = await client.send_request("get", f"/analysis/analysis-result/{analysis_result_id}")
    return AnalysisResult(**response.body)


async def get_analysis_results_by_ids_request(client: ProjectClient, analysis_result_ids: List[uuid.UUID]) -> List[AnalysisResult]:
    response = await client.send_request("post", "/analysis/analysis-results/by-ids", json={"analysis_result_ids": [str(id) for id in analysis_result_ids]})
    return [AnalysisResult(**result) for result in response.body]




async def create_notebook_section(client: ProjectClient, analysis_object_id: uuid.UUID, section_create: List[NotebookSectionCreate]) -> str:
    """
    Create a new notebook section. If no parent section is provided in the section_create object, the new section will be a top level section.

    Args:
        ctx (RunContext[AnalysisDeps]): The context of the analysis.
        analysis_object_id (uuid.UUID): The ID of the analysis object.
        section_create (List[NotebookSectionCreate]): The sections to create.
    """ 
    try:
        section_ids = []
        for section in section_create: # Must have synchronous creation of sections to avoid race conditions
            # logger.info("section: ", section)
            # logger.info("analysis_object_id: ", analysis_object_id)
            section_in_db = await create_section_request(client, analysis_object_id, section)
            # logger.info("section_in_db: ", section_in_db)
            section_ids.append(section_in_db.id)
        return f"Notebook sections successfully created. Section ids: {section_ids}"
    except Exception as e:
        return f"Error creating notebook section: {e}"


async def main():

    bearer_token = "eyJhbGciOiJFUzI1NiIsInR5cCI6IkpXVCJ9.eyJzdWIiOiI5NTQwNmFlNy1kYWQ3LTQxZDQtYjU0Ni1jNGJmZDZjMzRmY2QiLCJleHAiOjE3NTk5MjUyMTR9.2UIC028teiwLM7vipfDBmLJzVCN8tjcLMpmcz2jJU0YLe9fa6oMGvY0qt3PuFYNml7qSZR0Nlo6Zuo3G_tcgWQ"
    project_client = ProjectClient()
    project_client.set_bearer_token(bearer_token)
    project_id = "37ab3cab-f0fc-48dd-8dcd-3d5875a70cf3"

    # print(await get_analysis_objects_by_project_request(project_client, project_id))
    analysis_object_id = "08fbbafc-9e48-42d1-9098-d0a78bdee6f9"
    section_create = NotebookSectionCreate(
        analysis_object_id=analysis_object_id,
        section_name="Test section",
        section_description="Test description",
        parent_section_id=None
    )
    section_in_db = await create_notebook_section(project_client, analysis_object_id, [section_create])
    print(section_in_db)

if __name__ == "__main__":
    import asyncio
    
    asyncio.run(main())