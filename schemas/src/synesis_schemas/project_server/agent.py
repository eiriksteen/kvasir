from pydantic import BaseModel
from typing import List, Optional
from uuid import UUID


class RunSWERequest(BaseModel):
    run_id: UUID
    project_id: UUID
    prompt_content: str
    conversation_id: Optional[UUID] = None
    target_pipeline_id: Optional[UUID] = None
    input_data_source_ids: List[UUID] = []
    input_dataset_ids: List[UUID] = []
    input_model_entity_ids: List[UUID] = []
    input_analysis_ids: List[UUID] = []
    input_pipeline_ids: List[UUID] = []


class RunAnalysisRequest(BaseModel):
    run_id: UUID
    project_id: UUID
    prompt_content: str
    target_analysis_id: UUID
    input_data_source_ids: List[UUID] = []
    input_dataset_ids: List[UUID] = []
    input_analysis_ids: List[UUID] = []
    input_model_entity_ids: List[UUID] = []
    conversation_id: UUID | None = None


class RunExtractionRequest(BaseModel):
    project_id: UUID
    prompt_content: str
    run_id: Optional[UUID] = None
