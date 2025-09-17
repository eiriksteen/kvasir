from typing import List, Optional, Literal
from pydantic_ai import RunContext, ModelRetry
from pydantic import field_validator, BaseModel

from synesis_data_structures.time_series.definitions import get_first_level_structure_ids
from synesis_schemas.main_server import PipelineCreate, FunctionInputStructureCreate, FunctionOutputStructureCreate, FunctionOutputVariableCreate, ModelTaskBare


# Schema outputs


class FunctionsToImplementOutput(BaseModel):
    function_names: List[str]
    function_descriptions_brief: List[str]


class DetailedFunctionDescription(BaseModel):
    name: str
    description: str
    type: Literal["inference", "training", "computation"]
    input_structures: List[FunctionInputStructureCreate]
    output_structures: List[FunctionOutputStructureCreate]
    output_variables: List[FunctionOutputVariableCreate]
    output_models: List[ModelTaskBare]


class ImplementationFeedbackOutput(BaseModel):
    approved: bool
    feedback: Optional[str] = None

    @field_validator('feedback')
    @classmethod
    def validate_feedback_when_not_approved(cls, v, info):
        if not info.data.get('approved', True) and v is None:
            raise ValueError('Feedback is required when approved is False')
        return v


# Function outputs


async def submit_detailed_function_description_output(
    _: RunContext,
    result: DetailedFunctionDescription
) -> DetailedFunctionDescription:

    first_level_structure_ids = get_first_level_structure_ids()

    if len(result.input_structures) == 0:
        raise ModelRetry("No input structures provided!")

    if len(result.output_structures) == 0:
        raise ModelRetry("No output structures provided!")

    for input in result.input_structures:
        if input.structure_id not in first_level_structure_ids:
            raise ModelRetry(
                f"Invalid structure ID: {input.structure_id}, available structures: {first_level_structure_ids}")

    for output in result.output_structures:
        if output.structure_id not in first_level_structure_ids:
            raise ModelRetry(
                f"Invalid structure ID: {output.structure_id}, available structures: {first_level_structure_ids}")

    return result


async def submit_final_pipeline_output(
    _: RunContext,
    result: PipelineCreate
) -> PipelineCreate:

    # TODO: Implement
    # This will set up a docker container with the functions and run it on some dummy data to ensure it runs
    # Raises model retry if any error

    if len(result.functions) == 0:
        raise ModelRetry("No function IDs provided!")

    return result
