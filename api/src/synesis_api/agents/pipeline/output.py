import uuid
from typing import List, Optional
from pydantic_ai import RunContext, ModelRetry
from pydantic import field_validator

from synesis_api.base_schema import BaseSchema
from synesis_api.agents.pipeline.deps import PipelineAgentDeps
from synesis_api.modules.pipeline.service import check_function_ids_exist
from synesis_api.modules.pipeline.schema import FunctionInputCreate, FunctionOutputCreate
from synesis_data_structures.time_series.definitions import get_first_level_structure_ids


# Schema outputs


class SearchQueryOutput(BaseSchema):
    function_names: List[str]
    function_descriptions: List[str]


class FunctionsToImplementOutput(BaseSchema):
    function_names: List[str]
    function_descriptions_brief: List[str]


class DetailedFunctionDescription(BaseSchema):
    name: str
    description: str
    inputs: List[FunctionInputCreate]
    outputs: List[FunctionOutputCreate]


class ImplementationFeedbackOutput(BaseSchema):
    approved: bool
    feedback: Optional[str] = None

    @field_validator('feedback')
    @classmethod
    def validate_feedback_when_not_approved(cls, v, info):
        if not info.data.get('approved', True) and v is None:
            raise ValueError('Feedback is required when approved is False')
        return v


class FinalPipelineOutput(BaseSchema):
    name: str
    description: str
    function_ids: List[uuid.UUID]


# Function outputs


async def submit_detailed_function_description_output(
    ctx: RunContext[PipelineAgentDeps],
    result: DetailedFunctionDescription
) -> DetailedFunctionDescription:

    first_level_structure_ids = get_first_level_structure_ids()

    for input in result.inputs:
        if input.structure_id not in first_level_structure_ids:
            raise ModelRetry(f"Invalid structure ID: {input.structure_id}")

    for output in result.outputs:
        if output.structure_id not in first_level_structure_ids:
            raise ModelRetry(f"Invalid structure ID: {output.structure_id}")

    return result


async def submit_final_pipeline_output(
    ctx: RunContext[PipelineAgentDeps],
    result: FinalPipelineOutput
) -> FinalPipelineOutput:

    # TODO: Implement
    # This will set up a docker container with the functions and run it on some dummy data to ensure it runs
    # Raises model retry if any error

    if len(result.function_ids) == 0:
        raise ModelRetry("No function IDs provided!")

    if not await check_function_ids_exist(result.function_ids):
        raise ModelRetry("One or more function IDs do not exist!")

    return result
