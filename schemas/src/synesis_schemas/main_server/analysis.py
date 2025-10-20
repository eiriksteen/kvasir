from uuid import UUID
from datetime import datetime
from typing import List, Literal
from pydantic import BaseModel


# API schemas
class AnalysisResult(BaseModel):
    id: UUID
    analysis: str
    python_code: str | None = None
    input_variable: str | None = None
    output_variable: str | None = None
    next_type: Literal['analysis_result', 'notebook_section'] | None = None
    next_id: UUID | None = None
    section_id: UUID | None = None
    dataset_ids: List[UUID] = []
    data_source_ids: List[UUID] = []


class NotebookSection(BaseModel):
    id: UUID
    notebook_id: UUID
    section_name: str
    section_description: str | None = None
    next_type: Literal['analysis_result', 'notebook_section'] | None = None
    next_id: UUID | None = None
    parent_section_id: UUID | None = None
    notebook_sections: List['NotebookSection'] = []
    analysis_results: List[AnalysisResult] = []


class Notebook(BaseModel):
    id: UUID
    notebook_sections: List[NotebookSection] = []


class AnalysisObjectSmall(BaseModel):
    id: UUID
    project_id: UUID
    name: str
    description: str | None = None
    report_generated: bool = False
    created_at: datetime = datetime.now()


class Analysis(AnalysisObjectSmall):
    notebook: Notebook


class AnalysisStatusMessage(BaseModel):
    id: UUID
    run_id: UUID
    result: AnalysisResult
    created_at: datetime = datetime.now()


# DB schemas
class AnalysisObjectInDB(BaseModel):
    id: UUID
    project_id: UUID
    name: str
    description: str | None = None
    report_generated: bool = False
    created_at: datetime = datetime.now()
    user_id: UUID
    notebook_id: UUID


class NotebookInDB(BaseModel):
    id: UUID


class NotebookSectionInDB(BaseModel):
    id: UUID
    notebook_id: UUID
    section_name: str
    section_description: str | None = None
    next_type: Literal['analysis_result', 'notebook_section'] | None = None
    next_id: UUID | None = None
    parent_section_id: UUID | None = None


class AnalysisResultInDB(BaseModel):
    id: UUID
    analysis: str
    python_code: str | None = None
    input_variable: str | None = None
    output_variable: str | None = None
    next_type: Literal['analysis_result', 'notebook_section'] | None = None
    next_id: UUID | None = None
    section_id: UUID | None = None


class AnalysisResultDatasetRelationInDB(BaseModel):
    id: UUID
    analysis_result_id: UUID
    dataset_id: UUID


class NotebookSectionAnalysisResultRelationInDB(BaseModel):
    id: UUID
    notebook_section_id: UUID
    analysis_result_id: UUID


# Other schemas
class AnalysisObjectCreate(BaseModel):
    name: str
    project_id: UUID
    description: str | None = None


class AnalysisResultUpdate(BaseModel):
    analysis: str | None = None
    python_code: str | None = None


class NotebookSectionCreate(BaseModel):
    analysis_object_id: UUID
    section_name: str
    section_description: str | None = None
    parent_section_id: UUID | None = None


class AnalysisObjectList(BaseModel):
    analysis_objects: List[AnalysisObjectSmall]


class NotebookSectionUpdate(BaseModel):
    section_name: str | None = None
    section_description: str | None = None


class GenerateReportRequest(BaseModel):
    filename: str
    include_code: bool


class MoveRequest(BaseModel):
    new_section_id: UUID | None = None
    moving_element_type: Literal['analysis_result', 'notebook_section']
    moving_element_id: UUID
    next_element_type: Literal['analysis_result',
                               'notebook_section'] | None = None
    next_element_id: UUID | None = None


class AnalysisResultFindRequest(BaseModel):
    analysis_result_ids: List[UUID]
