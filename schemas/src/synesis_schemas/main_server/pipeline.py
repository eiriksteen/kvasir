from pydantic import BaseModel, model_validator
from typing import Optional, Literal, List
from datetime import datetime
from uuid import UUID

from .function import FunctionWithoutEmbedding
from .data_objects import ObjectGroup
from .runs import RunInDB

# DB models


class PipelineInDB(BaseModel):
    id: UUID
    user_id: UUID
    name: str
    python_function_name: str
    filename: str
    module_path: str
    description: str
    docstring: str
    args: dict
    args_schema: dict
    output_variables_schema: dict
    implementation_script_path: str
    args_dataclass_name: str
    input_dataclass_name: str
    output_dataclass_name: str
    output_variables_dataclass_name: str
    created_at: datetime
    updated_at: datetime


class ObjectGroupInPipelineInDB(BaseModel):
    pipeline_id: UUID
    object_group_id: UUID
    code_variable_name: str
    created_at: datetime
    updated_at: datetime


class FunctionInPipelineInDB(BaseModel):
    pipeline_id: UUID
    function_id: UUID
    created_at: datetime
    updated_at: datetime


class ModelEntityInPipelineInDB(BaseModel):
    model_entity_id: UUID
    pipeline_id: UUID
    code_variable_name: str
    created_at: datetime
    updated_at: datetime


class PipelinePeriodicScheduleInDB(BaseModel):
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
class PipelineOnEventScheduleInDB(BaseModel):
    id: UUID
    pipeline_id: UUID
    event_listener_script_path: str
    event_description: str
    created_at: datetime
    updated_at: datetime


class PipelineOutputObjectGroupDefinitionInDB(BaseModel):
    id: UUID
    pipeline_id: UUID
    name: str
    structure_id: str
    description: str
    output_entity_id_name: str
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


class PipelineGraphNodeInDB(BaseModel):
    id: UUID
    type: Literal['dataset', 'function', 'model_entity']
    pipeline_id: UUID
    created_at: datetime
    updated_at: datetime


class PipelineGraphEdgeInDB(BaseModel):
    from_node_id: UUID
    to_node_id: UUID
    created_at: datetime
    updated_at: datetime


class PipelineGraphDatasetNodeInDB(BaseModel):
    id: UUID
    dataset_id: UUID
    created_at: datetime
    updated_at: datetime


class PipelineGraphFunctionNodeInDB(BaseModel):
    id: UUID
    function_id: UUID
    created_at: datetime
    updated_at: datetime


class PipelineGraphModelEntityNodeInDB(BaseModel):
    id: UUID
    model_entity_id: UUID
    function_type: Literal["training", "inference"]
    created_at: datetime
    updated_at: datetime


# API models


class PipelineSources(BaseModel):
    dataset_ids: List[UUID]
    model_entity_ids: List[UUID]


class PipelineGraphNode(BaseModel):
    id: UUID
    entity_id: UUID
    type: Literal['dataset', 'function', 'model_entity']
    model_function_type: Optional[Literal["training", "inference"]] = None
    from_model_entity_ids: List[UUID]
    from_function_ids: List[UUID]
    from_dataset_ids: List[UUID]


class PipelineGraph(BaseModel):
    nodes: List[PipelineGraphNode]


class PipelineFull(PipelineInDB):
    functions: List[FunctionWithoutEmbedding]
    model_entities: List[ModelEntityInPipelineInDB]
    runs: List[RunInDB] = []
    periodic_schedules: List[PipelinePeriodicScheduleInDB] = []
    on_event_schedules: List[PipelineOnEventScheduleInDB] = []
    computational_graph: PipelineGraph
    sources: PipelineSources
    input_object_groups: List[ObjectGroup]
    output_object_group_definitions: List[PipelineOutputObjectGroupDefinitionInDB]


class PipelineRunStatusUpdate(BaseModel):
    status: Literal["running", "completed", "failed"]


class PipelineRunDatasetOutputCreate(BaseModel):
    dataset_id: UUID


class PipelineRunModelEntityOutputCreate(BaseModel):
    model_entity_id: UUID


# Create models

class ObjectGroupInPipelineCreate(BaseModel):
    object_group_id: UUID
    code_variable_name: str


class ModelEntityInPipelineCreate(BaseModel):
    model_entity_id: UUID
    code_variable_name: str


class PipelineOutputObjectGroupDefinitionCreate(BaseModel):
    name: str
    structure_id: str
    description: str
    output_entity_id_name: str


class PeriodicScheduleCreate(BaseModel):
    schedule_description: str
    cron_expression: str
    start_time: Optional[datetime] = None
    end_time: Optional[datetime] = None


class OnEventScheduleCreate(BaseModel):
    event_description: str


class PipelineNodeCreate(BaseModel):
    entity_id: UUID
    type: Literal['dataset', 'function', 'model_entity']
    model_function_type: Optional[Literal["training", "inference"]] = None
    from_model_entity_ids: List[UUID]
    from_function_ids: List[UUID]
    from_dataset_ids: List[UUID]


class PipelineGraphCreate(BaseModel):
    nodes: List[PipelineNodeCreate]


class PipelineCreate(BaseModel):
    name: str
    python_function_name: str
    filename: str
    docstring: str
    module_path: str
    description: str
    implementation_script_path: str
    args_dataclass_name: str
    input_dataclass_name: str
    output_dataclass_name: str
    output_variables_dataclass_name: str
    args_schema: dict
    args: dict
    output_variables_schema: dict
    periodic_schedules: List[PeriodicScheduleCreate]
    on_event_schedules: List[OnEventScheduleCreate]
    computational_graph: PipelineGraphCreate
    function_ids: List[UUID]
    input_model_entities: List[ModelEntityInPipelineCreate]
    input_object_groups: List[ObjectGroupInPipelineCreate]
    output_object_group_definitions: List[PipelineOutputObjectGroupDefinitionCreate]
