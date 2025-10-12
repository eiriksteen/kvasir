from pydantic import BaseModel
from typing import Literal
from uuid import UUID


class RunPipelineRequest(BaseModel):
    project_id: UUID
    pipeline_id: UUID


class PipelineRunStatusUpdate(BaseModel):
    status: Literal["running", "completed", "failed"]
