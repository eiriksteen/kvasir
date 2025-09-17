from typing import Optional, List, Literal
from uuid import UUID
from datetime import datetime
from pydantic import BaseModel

from .model import SUPPORTED_MODALITIES_TYPE
from .model import SUPPORTED_SOURCE_TYPE


class FunctionOutputVariableCreate(BaseModel):
    name: str
    python_type: str
    description: Optional[str] = None


class FunctionInputStructureCreate(BaseModel):
    structure_id: str
    name: str
    description: str
    required: bool


class FunctionOutputStructureCreate(BaseModel):
    structure_id: str
    name: str
    description: str


class FunctionCreate(BaseModel):
    name: str
    description: str
    implementation_script_path: str
    type: Literal["inference", "training", "computation"]
    input_structures: List[FunctionInputStructureCreate]
    output_structures: List[FunctionOutputStructureCreate]
    output_variables: List[FunctionOutputVariableCreate]
    setup_script_path: Optional[str] = None
    default_config: Optional[dict] = None


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


class _ModelTaskCreate(BaseModel):
    task: Literal["forecasting", "classification", "regression",
                  "clustering", "anomaly_detection", "generation", "segmentation"]
    inference_function_id: UUID
    training_function_id: UUID


class ModelCreate(BaseModel):
    name: str
    description: str
    modality: SUPPORTED_MODALITIES_TYPE
    source: SUPPORTED_SOURCE_TYPE
    programming_language_with_version: str
    setup_script_path: Optional[str] = None
    default_config: Optional[dict] = None
    model_tasks: List[_ModelTaskCreate]


class ModelResultCreate(BaseModel):
    model_task_id: UUID
    weights_path: str
    config: Optional[dict] = None
