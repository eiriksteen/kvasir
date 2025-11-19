import uuid
from typing import Literal, List, Optional
from datetime import datetime, timezone
from pydantic import BaseModel, Field


# Schemas

RUN_TYPE_LITERAL = Literal["swe", "analysis", "extraction", "kvasir", "chart"]
RESULT_TYPE_LITERAL = Literal["swe", "analysis", "extraction", "chart"]
RUN_STATUS_LITERAL = Literal["pending", "running",
                             "completed", "failed", "rejected", "waiting"]
MESSAGE_ROLE_LITERAL = Literal["swe", "analysis",
                               "kvasir", "user", "extraction", "chart"]
MESSAGE_TYPE_LITERAL = Literal["tool_call", "result", "error", "info", "chat"]


class RunBase(BaseModel):
    id: uuid.UUID
    run_name: str
    user_id: uuid.UUID
    type: RUN_TYPE_LITERAL
    status: RUN_STATUS_LITERAL
    description: Optional[str] = None
    project_id: Optional[uuid.UUID] = None
    started_at: datetime
    completed_at: Optional[datetime] = None


class Message(BaseModel):
    id: uuid.UUID
    content: str
    run_id: uuid.UUID
    role: MESSAGE_ROLE_LITERAL
    type: MESSAGE_TYPE_LITERAL
    created_at: datetime = Field(
        default_factory=lambda: datetime.now(timezone.utc))


class PydanticAIMessage(BaseModel):
    id: uuid.UUID
    run_id: uuid.UUID
    message_list: bytes
    created_at: datetime = Field(
        default_factory=lambda: datetime.now(timezone.utc))


class ResultsQueue(BaseModel):
    id: uuid.UUID
    run_id: uuid.UUID
    content: List[str]
    created_at: datetime


class DepsBase(BaseModel):
    id: uuid.UUID
    run_id: uuid.UUID
    type: RUN_TYPE_LITERAL
    content: str
    created_at: datetime


class ResultBase(BaseModel):
    id: uuid.UUID
    run_id: uuid.UUID
    type: RESULT_TYPE_LITERAL
    content: str
    created_at: datetime


# API schemas

class AnalysisRun(RunBase):
    analysis_id: uuid.UUID
    kvasir_run_id: uuid.UUID
    result: Optional[ResultBase] = None


class SweRun(RunBase):
    kvasir_run_id: uuid.UUID
    result: Optional[ResultBase] = None


# Create Schemas


class RunCreate(BaseModel):
    type: RUN_TYPE_LITERAL
    initial_status: RUN_STATUS_LITERAL = "pending"
    run_name: str = "New Run"
    project_id: uuid.UUID
    description: Optional[str] = None


class Context(BaseModel):
    data_source_ids: List[uuid.UUID] = Field(default_factory=list)
    dataset_ids: List[uuid.UUID] = Field(default_factory=list)
    analysis_ids: List[uuid.UUID] = Field(default_factory=list)
    pipeline_ids: List[uuid.UUID] = Field(default_factory=list)
    model_instantiated_ids: List[uuid.UUID] = Field(default_factory=list)


class MessageCreate(BaseModel):
    content: str
    run_id: uuid.UUID
    role: MESSAGE_ROLE_LITERAL
    type: MESSAGE_TYPE_LITERAL
    context: Context = Field(default_factory=Context)


class ResultsQueueCreate(BaseModel):
    run_id: uuid.UUID
    content: List[str]


class DepsCreate(BaseModel):
    run_id: uuid.UUID
    type: RUN_TYPE_LITERAL
    content: str


class ResultCreate(BaseModel):
    run_id: uuid.UUID
    type: RESULT_TYPE_LITERAL
    content: str
