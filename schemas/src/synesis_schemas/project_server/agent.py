from pydantic import BaseModel
from typing import List, Optional
from uuid import UUID
from pydantic_ai.messages import ModelMessage


class RunSWERequest(BaseModel):
    run_id: UUID
    project_id: UUID
    prompt_content: str
    conversation_id: UUID
    pipeline_id: UUID
    data_source_ids: List[UUID] = []
    dataset_ids: List[UUID] = []
    model_entity_ids: List[UUID] = []
    analysis_ids: List[UUID] = []


class RunAnalysisRequest(BaseModel):
    run_id: UUID
    project_id: UUID
    prompt_content: str
    analysis_id: UUID
    data_source_ids: List[UUID] = []
    dataset_ids: List[UUID] = []
    analysis_ids: List[UUID] = []
    model_entity_ids: List[UUID] = []
    conversation_id: UUID | None = None
