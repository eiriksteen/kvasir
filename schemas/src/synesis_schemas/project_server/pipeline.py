from pydantic import BaseModel
from uuid import UUID


class RunPipelineRequest(BaseModel):
    project_id: UUID
    conversation_id: UUID
    prompt_content: str


class PipelineCreate(BaseModel):
    pass


class FunctionCreate(BaseModel):
    pass
