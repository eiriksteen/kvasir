import uuid
from typing import Literal, List, Optional, Union
from datetime import datetime, timezone
from pydantic import BaseModel


# DB Models


RUN_TYPE_LITERAL = Literal["swe", "analysis"]


class RunInDB(BaseModel):
    id: uuid.UUID
    user_id: uuid.UUID
    type: RUN_TYPE_LITERAL
    status: Literal["pending", "running", "completed", "failed", "rejected"]
    run_name: str
    project_id: Optional[uuid.UUID] = None
    conversation_id: Optional[uuid.UUID] = None
    plan_and_deliverable_description_for_user: str
    plan_and_deliverable_description_for_agent: str
    questions_for_user: Optional[str] = None
    configuration_defaults_description: Optional[str] = None
    started_at: datetime
    completed_at: Optional[datetime] = None


class RunMessageInDB(BaseModel):
    id: uuid.UUID
    content: str
    run_id: uuid.UUID
    type:  Literal["tool_call", "result", "error"]
    created_at: datetime = datetime.now(timezone.utc)


class RunPydanticMessageInDB(BaseModel):
    id: uuid.UUID
    run_id: uuid.UUID
    message_list: bytes
    created_at: datetime = datetime.now(timezone.utc)


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
    model_entity_id: uuid.UUID
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
    model_entity_ids: List[uuid.UUID] = []
    pipeline_ids: List[uuid.UUID] = []
    analysis_ids: List[uuid.UUID] = []


class Run(RunInDB):
    inputs: Optional[RunEntityIds] = None
    outputs: Optional[RunEntityIds] = None


class MessageForLog(BaseModel):
    content: str
    type: Literal["tool_call", "result", "error"]
    write_to_db: int = 1
    target: Literal["redis", "taskiq", "both"] = "both"
    created_at: datetime = datetime.now(timezone.utc)


class CodeForLog(BaseModel):
    code: str
    filename: str
    target: Literal["redis", "taskiq", "both"] = "both"
    # cant do None because redis
    output: str = ""
    error: str = ""
    created_at: datetime = datetime.now(timezone.utc)


# Create Models


class RunCreate(BaseModel):
    type: RUN_TYPE_LITERAL
    initial_status: Literal["pending", "running",
                            "completed", "failed"] = "pending"
    run_name: str
    plan_and_deliverable_description_for_user: str
    plan_and_deliverable_description_for_agent: str
    questions_for_user: Optional[str] = None
    configuration_defaults_description: Optional[str] = None
    target_entity_id: Optional[uuid.UUID] = None
    project_id: Optional[uuid.UUID] = None
    conversation_id: Optional[uuid.UUID] = None
    data_sources_in_run: List[uuid.UUID] = []
    datasets_in_run: List[uuid.UUID] = []
    model_entities_in_run: List[uuid.UUID] = []
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
    status: Literal["running", "completed", "failed", "rejected"]
    summary: Optional[str] = None
