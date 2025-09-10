from pydantic import BaseModel
from typing import List
from uuid import UUID


class RunDataSourceAnalysisRequest(BaseModel):
    data_source_id: UUID
    file_path: str


class RunDataIntegrationRequest(BaseModel):
    project_id: UUID
    run_id: UUID
    conversation_id: UUID
    data_source_ids: List[UUID]
    prompt_content: str


class RunPipelineRequest(BaseModel):
    project_id: UUID
    run_id: UUID
    conversation_id: UUID
    prompt_content: str
