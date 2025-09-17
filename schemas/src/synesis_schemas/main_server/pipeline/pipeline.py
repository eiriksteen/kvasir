from uuid import UUID
from datetime import datetime
from typing import Optional, Literal, List
from pydantic import BaseModel


class PipelineInDB(BaseModel):
    id: UUID
    user_id: UUID
    name: str
    created_at: datetime
    updated_at: datetime
    description: Optional[str] = None


class PipelineRunInDB(BaseModel):
    id: UUID
    pipeline_id: UUID
    status: Literal["pending", "running", "completed", "failed"]
    start_time: datetime
    end_time: datetime
    created_at: datetime
    updated_at: datetime


class FunctionInDB(BaseModel):
    id: UUID
    name: str
    implementation_script_path: str
    created_at: datetime
    updated_at: datetime
    description: str
    embedding: List[float]
    type: Literal["inference", "training", "computation"]
    setup_script_path: Optional[str] = None
    default_config: Optional[dict] = None


class FunctionInPipelineInDB(BaseModel):
    id: UUID
    pipeline_id: UUID
    function_id: UUID
    position: int
    created_at: datetime
    updated_at: datetime
    config: Optional[dict] = None
