from uuid import UUID
from datetime import datetime, timezone
from typing import List, Literal
from pydantic import BaseModel, model_validator


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
    plot_urls: List[str] = []



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


class AnalysisInputEntities(BaseModel):
    dataset_ids: List[UUID] = []
    data_source_ids: List[UUID] = []
    model_entity_ids: List[UUID] = []
    analysis_ids: List[UUID] = []


class AnalysisSmall(BaseModel):
    id: UUID
    name: str
    description: str | None = None
    report_generated: bool = False
    created_at: datetime = datetime.now()
    inputs: AnalysisInputEntities


class Analysis(AnalysisSmall):
    notebook: Notebook
    inputs: AnalysisInputEntities
    description_for_agent: str


class AnalysisStatusMessage(BaseModel):
    id: UUID
    run_id: UUID
    section: NotebookSection | None = None
    analysis_result: AnalysisResult | None = None
    created_at: datetime = datetime.now()

    @model_validator(mode='after')
    def check_section_or_analysis_result(self) -> 'AnalysisStatusMessage':
        if self.section is None and self.analysis_result is None:
            raise ValueError("Either section or analysis_result must be set")
        return self


class GetAnalysesByIDsRequest(BaseModel):
    analysis_ids: List[UUID]

# DB schemas


class AnalysisInDB(BaseModel):
    id: UUID
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


class DatasetInAnalysisInDB(BaseModel):
    analysis_id: UUID
    dataset_id: UUID


class DataSourceInAnalysisInDB(BaseModel):
    analysis_id: UUID
    data_source_id: UUID


class ModelEntityInAnalysisInDB(BaseModel):
    analysis_id: UUID
    model_entity_id: UUID


class AnalysisFromPastAnalysisInDB(BaseModel):
    analysis_id: UUID
    past_analysis_id: UUID

# Other schemas


class AnalysisCreate(BaseModel):
    name: str
    description: str | None = None
    input_data_source_ids: List[UUID]
    input_dataset_ids: List[UUID]
    input_model_entity_ids: List[UUID]
    input_analysis_ids: List[UUID]


class AnalysisResultUpdate(BaseModel):
    analysis: str | None = None
    python_code: str | None = None


class NotebookSectionCreate(BaseModel):
    analysis_id: UUID
    section_name: str
    section_description: str | None = None
    parent_section_id: UUID | None = None


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
