from pydantic import BaseModel
from typing import Optional, Literal, List
from datetime import datetime
from uuid import UUID

from .function import FunctionBare

# DB models


class PipelineInDB(BaseModel):
    id: UUID
    user_id: UUID
    name: str
    created_at: datetime
    updated_at: datetime
    description: Optional[str] = None


class PipelineFromDatasetInDB(BaseModel):
    dataset_id: UUID
    pipeline_id: UUID
    created_at: datetime
    updated_at: datetime


class PipelineFromModelInDB(BaseModel):
    model_id: UUID
    pipeline_id: UUID
    created_at: datetime
    updated_at: datetime


class PipelineRunInDB(BaseModel):
    id: UUID
    pipeline_id: UUID
    status: Literal["pending", "running", "completed", "failed"]
    start_time: datetime
    end_time: datetime
    created_at: datetime
    updated_at: datetime


class FunctionInPipelineInDB(BaseModel):
    id: UUID
    pipeline_id: UUID
    function_id: UUID
    position: int
    created_at: datetime
    updated_at: datetime
    config: Optional[dict] = None


class PipelineRunObjectGroupResultInDB(BaseModel):
    id: UUID
    pipeline_run_id: UUID
    object_group_id: UUID
    created_at: datetime
    updated_at: datetime


class PipelineRunVariablesResultInDB(BaseModel):
    id: UUID
    pipeline_run_id: UUID
    variables_save_path: str
    created_at: datetime
    updated_at: datetime


class PeriodicScheduleInDB(BaseModel):
    id: UUID
    pipeline_id: UUID
    start_time: datetime
    end_time: datetime
    schedule_description: str
    cron_expression: str
    created_at: datetime
    updated_at: datetime


# Not yet supported
# Would need to have the SWE agent create a script to listen for the event, then deploy it at some frequency
class OnEventScheduleInDB(BaseModel):
    id: UUID
    pipeline_id: UUID
    event_listener_script_path: str
    event_description: str
    created_at: datetime
    updated_at: datetime


# API models


class PipelineSources(BaseModel):
    dataset_ids: List[UUID]
    model_ids: List[UUID]


class PipelineFull(PipelineInDB):
    functions: List[FunctionBare]
    runs: List[PipelineRunInDB] = []
    periodic_schedules: List[PeriodicScheduleInDB] = []
    on_event_schedules: List[OnEventScheduleInDB] = []
    sources: PipelineSources

# Create models


class _PeriodicScheduleCreate(BaseModel):
    schedule_description: str
    cron_expression: str
    start_time: Optional[datetime] = None
    end_time: Optional[datetime] = None


class _OnEventScheduleCreate(BaseModel):
    event_description: str


class _FunctionInPipelineCreate(BaseModel):
    function_id: UUID
    order: int
    config: Optional[dict] = None


class PipelineCreate(BaseModel):
    name: str
    description: str
    functions: List[_FunctionInPipelineCreate]
    periodic_schedules: List[_PeriodicScheduleCreate]
    on_event_schedules: List[_OnEventScheduleCreate]
