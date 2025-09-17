from uuid import UUID
from typing import List, Optional
from pydantic import BaseModel

from .io import (
    FunctionInputStructureInDB,
    FunctionOutputStructureInDB,
    FunctionOutputVariableInDB,
)
from .pipeline import (
    FunctionInDB,
    PipelineInDB,
    PipelineRunInDB,
)
from .schedule import (
    PeriodicScheduleInDB,
    OnEventScheduleInDB,
)
from .model import (
    SUPPORTED_MODALITIES_TYPE,
    SUPPORTED_TASK_TYPE,
)


class Function(FunctionInDB):
    input_structures: List[FunctionInputStructureInDB]
    output_structures: List[FunctionOutputStructureInDB]
    output_variables: List[FunctionOutputVariableInDB]


class FunctionBare(BaseModel):
    id: UUID
    name: str
    description: str
    input_structures: List[FunctionInputStructureInDB]
    output_structures: List[FunctionOutputStructureInDB]
    output_variables: List[FunctionOutputVariableInDB]
    default_config: Optional[dict] = None


class PipelineFull(PipelineInDB):
    functions: List[FunctionBare]
    runs: List[PipelineRunInDB] = []
    periodic_schedules: List[PeriodicScheduleInDB] = []
    on_event_schedules: List[OnEventScheduleInDB] = []


class ModelBare(BaseModel):
    id: UUID
    name: str
    description: str
    modality: SUPPORTED_MODALITIES_TYPE
    default_config: Optional[dict] = None


class ModelTaskBare(BaseModel):
    model_id: UUID
    task: SUPPORTED_TASK_TYPE
