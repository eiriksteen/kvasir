import uuid
from typing import List, Optional, Literal
from pydantic_ai import RunContext, ModelRetry
from pydantic import field_validator, model_validator, BaseModel

from synesis_data_structures.time_series.definitions import get_first_level_structure_ids
from synesis_schemas.main_server import (
    FunctionInputObjectGroupDefinitionCreate,
    FunctionOutputObjectGroupDefinitionCreate,
    PeriodicScheduleCreate,
    OnEventScheduleCreate,
    SearchFunctionsRequest,
    ModelEntityConfigUpdate,
    PipelineOutputObjectGroupDefinitionCreate,
    ObjectGroupInPipelineCreate,
    ModelEntityInPipelineCreate,
    ModelFunctionInputObjectGroupDefinitionCreate,
    ModelFunctionOutputObjectGroupDefinitionCreate,
)


# Search stage outputs


class SearchFunctionsOutput(BaseModel):
    query_request: Optional[SearchFunctionsRequest] = None


class FunctionsInPipelineOutput(BaseModel):
    existing_functions_to_use_names: Optional[List[str]] = None


# Model configuration stage outputs

class ModelConfiguration(BaseModel):
    model_entity_name: str
    update: ModelEntityConfigUpdate


# Pipeline implementation stage outputs

class PipelineImplementationSpec(BaseModel):
    name: str
    python_function_name: str
    docstring: str
    description: str
    args_dataclass_name: str
    input_dataclass_name: str
    output_dataclass_name: str
    output_variables_dataclass_name: str
    args_schema: dict
    args: dict
    output_variables_schema: dict
    periodic_schedules: List[PeriodicScheduleCreate]
    on_event_schedules: List[OnEventScheduleCreate]
    input_model_entities: List[ModelEntityInPipelineCreate]
    input_object_groups: List[ObjectGroupInPipelineCreate]
    output_object_group_definitions: List[PipelineOutputObjectGroupDefinitionCreate]


class ImplementationFeedbackOutput(BaseModel):
    approved: bool
    feedback: Optional[str] = None

    @field_validator('feedback')
    @classmethod
    def validate_feedback_when_not_approved(cls, v, info):
        if not info.data.get('approved', True) and v is None:
            raise ValueError('Feedback is required when approved is False')
        return v


# Pipeline implementation summary stage outputs


class FunctionImplementationSpec(BaseModel):
    name: str
    python_function_name: str
    filename: str
    docstring: str
    description: str
    args_schema: dict
    default_args: dict
    output_variables_schema: dict
    type: Literal["computation", "tool"]
    args_dataclass_name: str
    input_dataclass_name: str
    output_dataclass_name: str
    output_variables_dataclass_name: str
    input_object_groups: List[FunctionInputObjectGroupDefinitionCreate]
    output_object_group_definitions: List[FunctionOutputObjectGroupDefinitionCreate]
    setup_script_path: Optional[str] = None


class FunctionUpdateOutput(BaseModel):
    definition_id: uuid.UUID
    updates_made_description: str
    updated_python_function_name: Optional[str] = None
    updated_description: Optional[str] = None
    updated_docstring: Optional[str] = None
    updated_setup_script_path: Optional[str] = None
    updated_default_args: Optional[dict] = None
    updated_args_schema: Optional[dict] = None
    updated_output_variables_schema: Optional[dict] = None
    input_object_groups_to_add: Optional[
        List[FunctionInputObjectGroupDefinitionCreate]] = None
    output_object_group_definitions_to_add: Optional[
        List[FunctionOutputObjectGroupDefinitionCreate]] = None
    input_object_groups_to_remove: Optional[List[uuid.UUID]] = None
    output_object_group_definitions_to_remove: Optional[List[uuid.UUID]] = None


class ModelUpdateOutput(BaseModel):
    definition_id: uuid.UUID
    updates_made_description: str
    updated_python_class_name: Optional[str] = None
    updated_description: Optional[str] = None
    updated_docstring: Optional[str] = None
    updated_setup_script_path: Optional[str] = None
    updated_default_args: Optional[dict] = None
    updated_args_schema: Optional[dict] = None
    updated_output_variables_schema: Optional[dict] = None
    input_object_groups_to_add: Optional[
        List[ModelFunctionInputObjectGroupDefinitionCreate]] = None
    output_object_group_definitions_to_add: Optional[
        List[ModelFunctionOutputObjectGroupDefinitionCreate]] = None
    input_object_groups_to_remove: Optional[List[uuid.UUID]] = None
    output_object_group_definitions_to_remove: Optional[List[uuid.UUID]] = None


class PipelineNodeObjectGroupOutput(BaseModel):
    object_group_name: str
    is_pipeline_final_output: bool
    output_df_level_zero_index_name: str
    pipeline_output_variable_name: Optional[str] = None

    @model_validator(mode='after')
    def validate_pipeline_output_variable_name(self):
        if self.is_pipeline_final_output and self.pipeline_output_variable_name is None:
            raise ValueError(
                'pipeline_output_variable_name is required when is_pipeline_final_output is True'
            )
        return self


class PipelineNodeInGraph(BaseModel):
    name: str
    type: Literal['dataset', 'function', 'model_entity']
    model_function_type: Optional[Literal["training", "inference"]] = None
    from_model_entities: List[str]
    from_functions: List[str]
    from_datasets: List[str]


class PipelineGraphOutput(BaseModel):
    nodes: List[PipelineNodeInGraph]


async def submit_pipeline_spec_output(
    _: RunContext,
    result: PipelineImplementationSpec
) -> PipelineImplementationSpec:

    first_level_structure_ids = get_first_level_structure_ids()

    if len(result.input_object_groups) == 0:
        raise ModelRetry("No input groups provided!")

    for output in result.output_object_group_definitions:
        if output.structure_id not in first_level_structure_ids:
            raise ModelRetry(
                f"Invalid structure ID: {output.structure_id}, available structures: {first_level_structure_ids}")

    return result
