from typing import List, Optional, Literal
from pydantic_ai import RunContext, ModelRetry
from pydantic import field_validator, BaseModel

from synesis_data_structures.time_series.definitions import get_first_level_structure_ids
from synesis_schemas.main_server import (
    FunctionInputObjectGroupDefinitionCreate,
    FunctionOutputObjectGroupDefinitionCreate,
    FunctionOutputVariableDefinitionCreate,
    FunctionBare,
    PeriodicScheduleCreate,
    OnEventScheduleCreate,
    PipelineInputMapping,
    PipelineOutputMapping
)
from project_server.agents.swe.output import SWEAgentOutput


# Schema outputs


class FunctionToImplementOutput(BaseModel):
    name: str
    brief_description: str


class FunctionsInPipelineOutput(BaseModel):
    existing_functions_to_use_names: List[str]
    functions_to_implement: List[FunctionToImplementOutput]


class FunctionsInPipelineWithPopulatedFunctions(FunctionsInPipelineOutput):
    existing_functions: List[FunctionBare]


class DetailedFunctionDescription(BaseModel):
    name: str
    description: str
    type: Literal["inference", "training", "computation"]
    input_object_groups: List[FunctionInputObjectGroupDefinitionCreate]
    output_object_groups: List[FunctionOutputObjectGroupDefinitionCreate]
    output_variables: List[FunctionOutputVariableDefinitionCreate]
    args_dataclass_name: str
    input_dataclass_name: str
    output_dataclass_name: str
    output_variables_dataclass_name: str
    default_args: Optional[dict] = None


class ImplementationFeedbackOutput(BaseModel):
    approved: bool
    feedback: Optional[str] = None

    @field_validator('feedback')
    @classmethod
    def validate_feedback_when_not_approved(cls, v, info):
        if not info.data.get('approved', True) and v is None:
            raise ValueError('Feedback is required when approved is False')
        return v


class DetailedPipelineDescription(BaseModel):
    name: str
    description: str
    input_object_groups: List[FunctionInputObjectGroupDefinitionCreate]
    output_object_groups: List[FunctionOutputObjectGroupDefinitionCreate]
    output_variable_groups: List[FunctionOutputVariableDefinitionCreate]
    input_mapping: PipelineInputMapping
    output_mapping: PipelineOutputMapping
    args_dataclass_name: str
    input_dataclass_name: str
    output_dataclass_name: str
    output_variables_dataclass_name: str
    periodic_schedules: List[PeriodicScheduleCreate]
    on_event_schedules: List[OnEventScheduleCreate]
    args_dict: Optional[dict] = None


class MappingFromFunctionOutput(BaseModel):
    source_function_name: str
    source_object_group_variable: str


class MappingFromDatasetOutput(BaseModel):
    source_dataset_name: str
    source_object_group_variable: str


class InputVariableMappingOutput(BaseModel):
    to_function_input_object_group_variable: str
    from_function_output_object_group_variable: Optional[MappingFromFunctionOutput] = None
    from_dataset_object_group_variable: Optional[MappingFromDatasetOutput] = None


class FunctionModifiedOutput(BaseModel):
    updated_description: Optional[str] = None
    updated_default_args_dict: Optional[dict] = None
    input_object_group_variables_added: Optional[List[FunctionInputObjectGroupDefinitionCreate]] = None
    output_object_group_variables_added: Optional[List[FunctionOutputObjectGroupDefinitionCreate]] = None
    output_variable_group_variables_added: Optional[List[FunctionOutputVariableDefinitionCreate]] = None
    input_object_group_variables_removed: Optional[List[str]] = None
    output_object_group_variables_removed: Optional[List[str]] = None
    output_variable_group_variables_removed: Optional[List[str]] = None


class FunctionInPipelineOutput(BaseModel):
    function_name: str
    input_variable_mappings: List[InputVariableMappingOutput]
    output_object_group_variables_to_save: List[str]
    output_variable_group_variables_to_save: List[str]
    function_modified: Optional[FunctionModifiedOutput] = None


class PipelineAgentFinalOutput(DetailedPipelineDescription):
    functions: List[FunctionInPipelineOutput]
    swe_output: SWEAgentOutput


# Function outputs


async def submit_detailed_function_description_output(
    _: RunContext,
    result: DetailedFunctionDescription
) -> DetailedFunctionDescription:

    first_level_structure_ids = get_first_level_structure_ids()

    if len(result.input_object_groups) == 0:
        raise ModelRetry("No input structures provided!")

    if len(result.output_object_groups) == 0:
        raise ModelRetry("No output structures provided!")

    for input in result.input_object_groups:
        if input.structure_id not in first_level_structure_ids:
            raise ModelRetry(
                f"Invalid structure ID: {input.structure_id}, available structures: {first_level_structure_ids}")

    for output in result.output_object_groups:
        if output.structure_id not in first_level_structure_ids:
            raise ModelRetry(
                f"Invalid structure ID: {output.structure_id}, available structures: {first_level_structure_ids}")

    return result


async def submit_final_pipeline_output(
    _: RunContext,
    functions_in_pipeline: List[FunctionInPipelineOutput]
) -> List[FunctionInPipelineOutput]:

    if len(functions_in_pipeline) == 0:
        raise ModelRetry("No function IDs provided!")

    found_object_groups_to_save = False
    found_variable_groups_to_save = False
    for function in functions_in_pipeline:
        if len(function.input_variable_mappings) == 0:
            raise ModelRetry("No input variable mappings provided!")
        if len(function.output_object_group_variables_to_save) > 0:
            found_object_groups_to_save = True
        if len(function.output_variable_group_variables_to_save) > 0:
            found_variable_groups_to_save = True

        for input_variable_mapping in function.input_variable_mappings:
            if input_variable_mapping.from_function_output_object_group_variable is None and input_variable_mapping.from_dataset_object_group_variable is None:
                raise ModelRetry(
                    "The input variable must come from either a function data output object group or a dataset object group!")

    if not found_object_groups_to_save and not found_variable_groups_to_save:
        raise ModelRetry(
            "We need to save at least one object group or one variable group!")

    return functions_in_pipeline
