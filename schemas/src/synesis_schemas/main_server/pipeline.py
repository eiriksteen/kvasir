from uuid import UUID
from datetime import datetime
from typing import Optional, Dict, Any, List, Literal
from pydantic import BaseModel


# DB Schemas

class PipelineInDB(BaseModel):
    id: UUID
    user_id: UUID
    name: str
    created_at: datetime
    updated_at: datetime
    description: Optional[str] = None


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
    setup_script_path: Optional[str] = None
    default_config: Optional[dict] = None


class FunctionInputInDB(BaseModel):
    id: UUID
    position: int
    function_id: UUID
    structure_id: str
    name: str
    required: bool
    created_at: datetime
    updated_at: datetime
    description: Optional[str] = None


class FunctionOutputInDB(BaseModel):
    id: UUID
    position: int
    function_id: UUID
    structure_id: str
    name: str
    created_at: datetime
    updated_at: datetime
    description: Optional[str] = None


class FunctionInPipelineInDB(BaseModel):
    id: UUID
    pipeline_id: UUID
    function_id: UUID
    position: int
    created_at: datetime
    updated_at: datetime
    config: Optional[dict] = None


class DataObjectComputedFromFunctionInDB(BaseModel):
    id: UUID
    data_object_id: UUID
    function_id: UUID
    created_at: datetime
    updated_at: datetime


class ModalityInDB(BaseModel):
    id: UUID
    name: str
    created_at: datetime
    updated_at: datetime
    description: Optional[str] = None


class TaskInDB(BaseModel):
    id: UUID
    name: str
    created_at: datetime
    updated_at: datetime
    description: Optional[str] = None


class SourceInDB(BaseModel):
    id: UUID
    name: str
    created_at: datetime
    updated_at: datetime
    description: Optional[str] = None


class ProgrammingLanguageInDB(BaseModel):
    id: UUID
    name: str
    created_at: datetime
    updated_at: datetime
    description: Optional[str] = None


class ProgrammingLanguageVersionInDB(BaseModel):
    id: UUID
    programming_language_id: UUID
    version: str
    created_at: datetime
    updated_at: datetime


class ModelInDB(BaseModel):
    id: UUID
    name: str
    description: str
    owner_id: UUID
    public: bool
    modality_id: UUID
    source_id: UUID
    programming_language_version_id: UUID
    setup_script_path: str
    input_description: str
    output_description: str
    config_parameters: Dict[str, Any]
    created_at: datetime
    updated_at: datetime


class ModelTaskInDB(BaseModel):
    id: UUID
    model_id: UUID
    task_id: UUID
    inference_script_path: str
    training_script_path: str
    inference_function_id: UUID
    training_function_id: UUID
    created_at: datetime
    updated_at: datetime


# Create schemas

class FunctionInputCreate(BaseModel):
    structure_id: str
    name: str
    description: str
    required: bool


class FunctionOutputCreate(BaseModel):
    structure_id: str
    name: str
    description: str


class PeriodicScheduleCreate(BaseModel):
    schedule_description: str
    cron_expression: str
    start_time: Optional[datetime] = None
    end_time: Optional[datetime] = None


class OnEventScheduleCreate(BaseModel):
    event_description: str


class FunctionCreate(BaseModel):
    name: str
    description: str
    implementation_script: str
    inputs: List[FunctionInputCreate]
    outputs: List[FunctionOutputCreate]
    setup_script: Optional[str] = None
    config_dict: Optional[dict] = None


class PipelineCreate(BaseModel):
    name: str
    description: str
    function_ids: List[UUID]
    function_configs: List[dict]
    periodic_schedules: List[PeriodicScheduleCreate]
    on_event_schedules: List[OnEventScheduleCreate]


# API schemas

class Function(FunctionInDB):
    inputs: List[FunctionInputInDB]
    outputs: List[FunctionOutputInDB]


class FunctionWithoutEmbedding(BaseModel):
    id: UUID
    name: str
    implementation_script_path: str
    created_at: datetime
    updated_at: datetime
    description: str
    inputs: List[FunctionInputInDB]
    outputs: List[FunctionOutputInDB]
    setup_script_path: Optional[str] = None
    default_config: Optional[dict] = None


class PipelineFull(PipelineInDB):
    functions: List[FunctionWithoutEmbedding]
    runs: List[PipelineRunInDB] = []
    periodic_schedules: List[PeriodicScheduleInDB] = []
    on_event_schedules: List[OnEventScheduleInDB] = []
