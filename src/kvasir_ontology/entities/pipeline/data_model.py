from pydantic import BaseModel
from typing import Optional, Literal, List
from datetime import datetime
from uuid import UUID


PIPELINE_RUN_STATUS_LITERAL = Literal["running", "completed", "failed"]

# DB models


class PipelineBase(BaseModel):
    id: UUID
    user_id: UUID
    name: str
    description: Optional[str] = None
    created_at: datetime
    updated_at: datetime


class PipelineImplementationBase(BaseModel):
    id: UUID
    python_function_name: str
    docstring: str
    description: Optional[str] = None
    args_schema: dict
    default_args: dict
    output_variables_schema: dict
    implementation_script_path: str
    created_at: datetime
    updated_at: datetime


class PipelineRunBase(BaseModel):
    id: UUID
    args: dict
    pipeline_id: UUID
    output_variables: dict
    name: Optional[str] = None
    description: Optional[str] = None
    status: PIPELINE_RUN_STATUS_LITERAL
    execution_command: Optional[str] = None
    terminal_output: Optional[str] = None
    start_time: datetime
    end_time: Optional[datetime] = None
    created_at: datetime
    updated_at: datetime


# API models


class Pipeline(PipelineBase):
    runs: List[PipelineRunBase] = []
    implementation: Optional[PipelineImplementationBase] = None


# Create models


class PipelineImplementationCreate(BaseModel):
    python_function_name: str
    docstring: str
    description: str
    args_schema: dict
    default_args: dict
    output_variables_schema: dict
    implementation_script_path: str
    pipeline_id: UUID


class PipelineRunCreate(BaseModel):
    name: str
    args: dict
    pipeline_id: UUID
    output_variables: dict = {}
    description: Optional[str] = None
    status: PIPELINE_RUN_STATUS_LITERAL = "running"
    execution_command: Optional[str] = None
    terminal_output: Optional[str] = None


class PipelineCreate(BaseModel):
    name: str
    description: Optional[str] = None
    implementation_create: Optional[PipelineImplementationCreate] = None
    runs_create: Optional[List[PipelineRunCreate]] = None
