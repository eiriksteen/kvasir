from pydantic import BaseModel
from uuid import UUID
from typing import List


class RunPipelineRequest(BaseModel):
    project_id: UUID
    conversation_id: UUID
    prompt_content: str
    input_dataset_ids: List[UUID]
    input_model_entity_ids: List[UUID] = []


class PipelineCreate(BaseModel):
    pass


class FunctionCreate(BaseModel):
    pass
