from pydantic import BaseModel, model_validator
from typing import Optional, Literal, List
from datetime import datetime
from uuid import UUID

from .function import FunctionWithoutEmbedding
from .code import ScriptCreate, ScriptInDB

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
    args: dict
    args_schema: dict
    output_variables_schema: dict
    implementation_script_id: UUID
    created_at: datetime
    updated_at: datetime


class DataSourceInPipelineInDB(BaseModel):
    data_source_id: UUID
    pipeline_id: UUID
    created_at: datetime
    updated_at: datetime


class DatasetInPipelineInDB(BaseModel):
    dataset_id: UUID
    pipeline_id: UUID
    created_at: datetime
    updated_at: datetime


class ModelEntityInPipelineInDB(BaseModel):
    model_entity_id: UUID
    pipeline_id: UUID
    created_at: datetime
    updated_at: datetime


class AnalysisInPipelineInDB(BaseModel):
    analysis_id: UUID
    pipeline_id: UUID
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
    status: Literal["running", "completed", "failed"]
    start_time: datetime
    end_time: Optional[datetime] = None
    created_at: datetime
    updated_at: datetime


class PipelineOutputDatasetInDB(BaseModel):
    pipeline_id: UUID
    dataset_id: UUID
    created_at: datetime
    updated_at: datetime


class PipelineOutputModelEntityInDB(BaseModel):
    pipeline_id: UUID
    model_entity_id: UUID
    created_at: datetime
    updated_at: datetime


# API models


class PipelineInputEntities(BaseModel):
    data_source_ids: List[UUID] = []
    dataset_ids: List[UUID] = []
    model_entity_ids: List[UUID] = []
    analysis_ids: List[UUID] = []


class PipelineOutputEntities(BaseModel):
    dataset_ids: List[UUID]
    model_entity_ids: List[UUID]


class PipelineImplementation(PipelineImplementationInDB):
    functions: List[FunctionWithoutEmbedding]
    implementation_script: ScriptInDB
    runs: List[PipelineRunInDB] = []


class Pipeline(PipelineInDB):
    inputs: PipelineInputEntities
    outputs: PipelineOutputEntities
    implementation: Optional[PipelineImplementation] = None


class PipelineRunStatusUpdate(BaseModel):
    status: Literal["running", "completed", "failed"]


class PipelineRunDatasetOutputCreate(BaseModel):
    dataset_id: UUID


class PipelineRunModelEntityOutputCreate(BaseModel):
    model_entity_id: UUID


# Create models


class PipelineCreate(BaseModel):
    name: str
    description: Optional[str] = None
    input_data_source_ids: List[UUID]
    input_dataset_ids: List[UUID]
    input_model_entity_ids: List[UUID]
    input_analysis_ids: List[UUID] = []


class PipelineImplementationCreate(BaseModel):
    python_function_name: str
    docstring: str
    description: str
    args_schema: dict
    args: dict
    output_variables_schema: dict
    function_ids: List[UUID]
    implementation_script_create: ScriptCreate
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
