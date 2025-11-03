from pydantic import BaseModel, model_validator
from typing import Optional, Literal, List
from datetime import datetime
from uuid import UUID

from .function import FunctionWithoutEmbedding


PIPELINE_RUN_STATUS_LITERAL = Literal["running", "completed", "failed"]

# DB models


class PipelineInDB(BaseModel):
    id: UUID
    user_id: UUID
    name: str
    description: str
    created_at: datetime
    updated_at: datetime


class PipelineImplementationInDB(BaseModel):
    id: UUID
    python_function_name: str
    docstring: str
    description: str
    args_schema: dict
    default_args: dict
    output_variables_schema: dict
    implementation_script_path: str
    created_at: datetime
    updated_at: datetime


class FunctionInPipelineInDB(BaseModel):
    pipeline_id: UUID
    function_id: UUID
    created_at: datetime
    updated_at: datetime


class PipelineRunInDB(BaseModel):
    id: UUID
    pipeline_id: UUID
    name: Optional[str] = None
    description: Optional[str] = None
    status: PIPELINE_RUN_STATUS_LITERAL
    args: dict
    output_variables: dict
    start_time: datetime
    end_time: Optional[datetime] = None
    created_at: datetime
    updated_at: datetime


# API models


class PipelineImplementation(PipelineImplementationInDB):
    functions: List[FunctionWithoutEmbedding]


class Pipeline(PipelineInDB):
    runs: List[PipelineRunInDB] = []
    implementation: Optional[PipelineImplementation] = None


class PipelineRunStatusUpdate(BaseModel):
    status: PIPELINE_RUN_STATUS_LITERAL


# Create models


class PipelineCreate(BaseModel):
    name: str
    description: Optional[str] = None


class PipelineImplementationCreate(BaseModel):
    python_function_name: str
    docstring: str
    description: str
    args_schema: dict
    default_args: dict
    output_variables_schema: dict
    function_ids: List[UUID]
    implementation_script_path: str
    pipeline_id: Optional[UUID] = None
    pipeline_create: Optional[PipelineCreate] = None

    @model_validator(mode='after')
    def check_pipeline_reference(self):
        if self.pipeline_id is None and self.pipeline_create is None:
            raise ValueError(
                'Either pipeline_id or pipeline_create must be provided')
        if self.pipeline_id is not None and self.pipeline_create is not None:
            raise ValueError(
                'Only one of pipeline_id or pipeline_create should be provided, not both')
        return self


class PipelineRunCreate(BaseModel):
    name: str
    project_id: UUID
    pipeline_id: UUID
    args: dict
    output_variables: dict = {}
    description: Optional[str] = None
    conversation_id: Optional[UUID] = None
    run_id: Optional[UUID] = None
    status: PIPELINE_RUN_STATUS_LITERAL = "running"


class GetPipelinesByIDsRequest(BaseModel):
    pipeline_ids: List[UUID]


class PipelineRunStatusUpdate(BaseModel):
    status: PIPELINE_RUN_STATUS_LITERAL


class PipelineRunOutputVariablesUpdate(BaseModel):
    pipeline_run_id: UUID
    # Default, add the key, if key exists, update the value
    new_output_variables: dict
