from pydantic import BaseModel
from typing import List, Optional
from uuid import UUID


class RunDataSourceAnalysisAgentRequest(BaseModel):
    data_source_id: UUID
    file_path: str


class RunDataIntegrationAgentRequest(BaseModel):
    run_id: UUID
    project_id: UUID
    conversation_id: UUID
    data_source_ids: List[UUID]
    prompt_content: str


class RunPipelineAgentRequest(BaseModel):
    run_id: UUID
    project_id: UUID
    conversation_id: UUID
    prompt_content: str
    input_dataset_ids: List[UUID]
    input_model_entity_ids: List[UUID]


class RunModelIntegrationAgentRequest(BaseModel):
    run_id: UUID
    project_id: UUID
    conversation_id: UUID
    prompt_content: str
    public: bool
