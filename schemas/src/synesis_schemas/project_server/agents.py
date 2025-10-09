from pydantic import BaseModel
from typing import List, Optional
from uuid import UUID
from pydantic_ai.messages import ModelMessage


class RunDataSourceAnalysisRequest(BaseModel):
    data_source_id: UUID
    file_path: str


class RunDataIntegrationRequest(BaseModel):
    project_id: UUID
    conversation_id: UUID
    data_source_ids: List[UUID]
    prompt_content: str


class RunPipelineRequest(BaseModel):
    project_id: UUID
    conversation_id: UUID
    prompt_content: str


class RunModelIntegrationRequest(BaseModel):
    project_id: UUID
    conversation_id: UUID
    prompt_content: str
    public: bool

class RunAnalysisRequest(BaseModel):
    project_id: UUID
    dataset_ids: List[UUID] = []
    analysis_ids: List[UUID] = []
    automation_ids: List[UUID] = []
    prompt: str | None = None
    user_id: UUID
    message_history: List[ModelMessage] = []
    conversation_id: UUID | None = None
    context_message: str
    run_id: UUID | None = None