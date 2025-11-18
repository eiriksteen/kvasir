import uuid
from typing import Literal, List, Optional, Union
from datetime import datetime, timezone
from pydantic import BaseModel, Field


# DB Models


RUN_TYPE_LITERAL = Literal["swe", "analysis", "extraction", "kvasir"]
RUN_STATUS_LITERAL = Literal["pending", "running",
                             "completed", "failed", "rejected", "waiting"]


class RunInDB(BaseModel):
    id: uuid.UUID
    run_name: str
    user_id: uuid.UUID
    type: RUN_TYPE_LITERAL
    status: RUN_STATUS_LITERAL
    description: Optional[str] = None
    project_id: Optional[uuid.UUID] = None
    conversation_id: Optional[uuid.UUID] = None
    configuration_defaults_description: Optional[str] = None
    started_at: datetime
    completed_at: Optional[datetime] = None


class RunMessageInDB(BaseModel):
    id: uuid.UUID
    content: str
    run_id: uuid.UUID
    type:  Literal["tool_call", "result", "error"]
    created_at: datetime = Field(
        default_factory=lambda: datetime.now(timezone.utc))


class RunPydanticMessageInDB(BaseModel):
    id: uuid.UUID
    run_id: uuid.UUID
    message_list: bytes
    created_at: datetime = Field(
        default_factory=lambda: datetime.now(timezone.utc))


class DataSourceInRunInDB(BaseModel):
    run_id: uuid.UUID
    data_source_id: uuid.UUID
    created_at: datetime


class DatasetInRunInDB(BaseModel):
    run_id: uuid.UUID
    dataset_id: uuid.UUID
    created_at: datetime


class ModelEntityInRunInDB(BaseModel):
    run_id: uuid.UUID
    model_instantiated_id: uuid.UUID
    created_at: datetime


class PipelineInRunInDB(BaseModel):
    run_id: uuid.UUID
    pipeline_id: uuid.UUID
    created_at: datetime


class AnalysisInRunInDB(BaseModel):
    run_id: uuid.UUID
    analysis_id: uuid.UUID
    created_at: datetime


class AnalysisFromRunInDB(BaseModel):
    run_id: uuid.UUID
    analysis_id: uuid.UUID
    created_at: datetime


class PipelineFromRunInDB(BaseModel):
    run_id: uuid.UUID
    pipeline_id: uuid.UUID
    created_at: datetime


# API Models


class RunEntityIds(BaseModel):
    data_source_ids: List[uuid.UUID] = []
    dataset_ids: List[uuid.UUID] = []
    model_instantiated_ids: List[uuid.UUID] = []
    pipeline_ids: List[uuid.UUID] = []
    analysis_ids: List[uuid.UUID] = []


class Run(RunInDB):
    inputs: Optional[RunEntityIds] = None
    outputs: Optional[RunEntityIds] = None


# Create Models


class RunCreate(BaseModel):
    id: Optional[uuid.UUID] = None
    type: RUN_TYPE_LITERAL
    initial_status: RUN_STATUS_LITERAL = "pending"
    run_name: str
    configuration_defaults_description: Optional[str] = None
    target_entity_id: Optional[uuid.UUID] = None
    project_id: Optional[uuid.UUID] = None
    conversation_id: Optional[uuid.UUID] = None
    data_sources_in_run: List[uuid.UUID] = []
    datasets_in_run: List[uuid.UUID] = []
    models_instantiated_in_run: List[uuid.UUID] = []
    pipelines_in_run: List[uuid.UUID] = []
    analyses_in_run: List[uuid.UUID] = []


class RunMessageCreate(BaseModel):
    type: Literal["tool_call", "result", "error"]
    content: str
    run_id: uuid.UUID


class RunMessageCreatePydantic(BaseModel):
    content: bytes
    run_id: uuid.UUID


# Update Models

class RunStatusUpdate(BaseModel):
    run_id: uuid.UUID
    status: RUN_STATUS_LITERAL
    summary: Optional[str] = None
