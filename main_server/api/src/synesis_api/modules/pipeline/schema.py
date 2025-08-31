from uuid import UUID
from datetime import datetime
from typing import Optional, Dict, Any, List, Literal
from synesis_api.base_schema import BaseSchema


# DB Schemas

class PipelineInDB(BaseSchema):
    id: UUID
    user_id: UUID
    name: str
    created_at: datetime
    updated_at: datetime
    description: Optional[str] = None


class PeriodicScheduleInDB(BaseSchema):
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
class OnEventScheduleInDB(BaseSchema):
    id: UUID
    pipeline_id: UUID
    event_listener_script_path: str
    event_description: str
    created_at: datetime
    updated_at: datetime


class PipelineRunInDB(BaseSchema):
    id: UUID
    pipeline_id: UUID
    status: Literal["pending", "running", "completed", "failed"]
    start_time: datetime
    end_time: datetime
    created_at: datetime
    updated_at: datetime


class FunctionInDB(BaseSchema):
    id: UUID
    name: str
    implementation_script_path: str
    created_at: datetime
    updated_at: datetime
    description: str
    embedding: List[float]
    setup_script_path: Optional[str] = None
    default_config: Optional[dict] = None


class FunctionInputInDB(BaseSchema):
    id: UUID
    position: int
    function_id: UUID
    structure_id: str
    name: str
    required: bool
    created_at: datetime
    updated_at: datetime
    description: Optional[str] = None


class FunctionOutputInDB(BaseSchema):
    id: UUID
    position: int
    function_id: UUID
    structure_id: str
    name: str
    created_at: datetime
    updated_at: datetime
    description: Optional[str] = None


class FunctionInPipelineInDB(BaseSchema):
    id: UUID
    pipeline_id: UUID
    function_id: UUID
    position: int
    created_at: datetime
    updated_at: datetime
    config: Optional[dict] = None


class DataObjectComputedFromFunctionInDB(BaseSchema):
    id: UUID
    data_object_id: UUID
    function_id: UUID
    created_at: datetime
    updated_at: datetime


class ModalityInDB(BaseSchema):
    id: UUID
    name: str
    created_at: datetime
    updated_at: datetime
    description: Optional[str] = None


class TaskInDB(BaseSchema):
    id: UUID
    name: str
    created_at: datetime
    updated_at: datetime
    description: Optional[str] = None


class SourceInDB(BaseSchema):
    id: UUID
    name: str
    created_at: datetime
    updated_at: datetime
    description: Optional[str] = None


class ProgrammingLanguageInDB(BaseSchema):
    id: UUID
    name: str
    created_at: datetime
    updated_at: datetime
    description: Optional[str] = None


class ProgrammingLanguageVersionInDB(BaseSchema):
    id: UUID
    programming_language_id: UUID
    version: str
    created_at: datetime
    updated_at: datetime


class ModelInDB(BaseSchema):
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


class ModelTaskInDB(BaseSchema):
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

class FunctionInputCreate(BaseSchema):
    structure_id: str
    name: str
    description: str
    required: bool


class FunctionOutputCreate(BaseSchema):
    structure_id: str
    name: str
    description: str


class PeriodicScheduleCreate(BaseSchema):
    schedule_description: str
    cron_expression: str
    start_time: Optional[datetime] = None
    end_time: Optional[datetime] = None


class OnEventScheduleCreate(BaseSchema):
    event_description: str


# API schemas

class Function(FunctionInDB):
    inputs: List[FunctionInputInDB]
    outputs: List[FunctionOutputInDB]


class FunctionWithoutEmbedding(BaseSchema):
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
