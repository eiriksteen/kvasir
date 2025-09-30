from pydantic import BaseModel, model_validator
from typing import Optional, Literal, List
from datetime import datetime
from uuid import UUID

from .function import FunctionBare
from .data_objects import ObjectGroupCreate, VariableGroupCreate

# DB models


class PipelineInDB(BaseModel):
    id: UUID
    user_id: UUID
    name: str
    implementation_script_path: str
    args_dataclass_name: str
    input_dataclass_name: str
    output_dataclass_name: str
    output_variables_dataclass_name: str
    created_at: datetime
    updated_at: datetime
    description: Optional[str] = None
    args_dict: Optional[dict] = None


class PipelineFromDatasetInDB(BaseModel):
    dataset_id: UUID
    pipeline_id: UUID
    created_at: datetime
    updated_at: datetime


class PipelineFromModelEntityInDB(BaseModel):
    model_entity_id: UUID
    pipeline_id: UUID
    created_at: datetime
    updated_at: datetime


class PipelineOutputDatasetInDB(BaseModel):
    dataset_id: UUID
    pipeline_id: UUID
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


class FunctionInPipelineInDB(BaseModel):
    id: UUID
    pipeline_id: UUID
    function_id: UUID
    created_at: datetime
    updated_at: datetime


class FunctionInPipelineObjectGroupMappingInDB(BaseModel):
    id: UUID
    pipeline_id: UUID
    to_function_input_object_group_id: UUID
    from_function_output_object_group_id: Optional[UUID] = None
    created_at: datetime
    updated_at: datetime


class PipelineObjectGroupOutputToSaveInDB(BaseModel):
    pipeline_id: UUID
    object_group_desc_id: UUID
    created_at: datetime
    updated_at: datetime


class PipelineVariableGroupOutputToSaveInDB(BaseModel):
    pipeline_id: UUID
    variable_group_desc_id: UUID
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


class PipelineRunObjectGroupResultInDB(BaseModel):
    id: UUID
    pipeline_run_id: UUID
    object_group_id: UUID
    output_to_save_id: UUID
    created_at: datetime
    updated_at: datetime


class PipelineRunVariableGroupResultInDB(BaseModel):
    id: UUID
    pipeline_run_id: UUID
    variable_group_id: UUID
    output_to_save_id: UUID
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
    model_entity_ids: List[UUID]


class PipelineFull(PipelineInDB):
    functions: List[FunctionBare]
    runs: List[PipelineRunInDB] = []
    periodic_schedules: List[PeriodicScheduleInDB] = []
    on_event_schedules: List[OnEventScheduleInDB] = []
    sources: PipelineSources


class DatasetObjectGroupInputMapping(BaseModel):
    dataset_name: str
    dataset_object_group_name: str
    pipeline_input_variable_name: str


class ModelEntityInputMapping(BaseModel):
    pipeline_input_weights_dir_variable_name: str
    # If none, we create one
    model_entity_weights_dir_name: Optional[str] = None


class PipelineInputMapping(BaseModel):
    from_dataset_object_groups: List[DatasetObjectGroupInputMapping]
    from_model_entities: List[ModelEntityInputMapping]


class PipelineOutputObjectGroupMapping(BaseModel):
    output_object_group_variable_name: str
    output_create: ObjectGroupCreate


class PipelineOutputVariableGroupMapping(BaseModel):
    output_variable_group_variable_name: str
    output_create: VariableGroupCreate


class PipelineOutputMapping(BaseModel):
    output_object_groups: List[PipelineOutputObjectGroupMapping]
    output_variable_groups: List[PipelineOutputVariableGroupMapping]


# Create models


class PeriodicScheduleCreate(BaseModel):
    schedule_description: str
    cron_expression: str
    start_time: Optional[datetime] = None
    end_time: Optional[datetime] = None


class OnEventScheduleCreate(BaseModel):
    event_description: str


class InputVariableMappingCreate(BaseModel):
    to_function_input_object_group_id: UUID
    from_function_output_object_group_id: Optional[UUID] = None
    from_dataset_object_group_id: Optional[UUID] = None


class FunctionInPipelineCreate(BaseModel):
    function_id: UUID
    input_variable_mappings: List[InputVariableMappingCreate]
    output_object_groups_to_save_ids: List[UUID]
    output_variable_groups_to_save_ids: List[UUID]


class PipelineCreate(BaseModel):
    name: str
    description: str
    implementation_script_path: str
    args_dataclass_name: str
    input_dataclass_name: str
    output_dataclass_name: str
    output_variables_dataclass_name: str
    functions: List[FunctionInPipelineCreate]
    periodic_schedules: List[PeriodicScheduleCreate]
    on_event_schedules: List[OnEventScheduleCreate]
    input_dataset_ids: List[UUID]
    args_dict: Optional[dict] = None
    input_model_entity_ids: Optional[List[UUID]] = None
