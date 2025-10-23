from pydantic import BaseModel
from typing import Literal, Optional
from uuid import UUID


class RunPipelineRequest(BaseModel):
    project_id: UUID
    pipeline_id: UUID
    run_id: Optional[UUID] = None


class PipelineRunStatusUpdate(BaseModel):
    status: Literal["running", "completed", "failed"]
