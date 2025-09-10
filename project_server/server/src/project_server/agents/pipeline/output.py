import uuid
from typing import List, Optional
from datetime import datetime
from pydantic_ai import RunContext, ModelRetry
from pydantic import field_validator, BaseModel

from synesis_data_structures.time_series.definitions import get_first_level_structure_ids


# Schema outputs


class SearchQueryOutput(BaseModel):
    function_names: List[str]
    function_descriptions: List[str]


class FunctionsToImplementOutput(BaseModel):
    function_names: List[str]
    function_descriptions_brief: List[str]


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


class DetailedFunctionDescription(BaseModel):
    name: str
    description: str
    inputs: List[FunctionInputCreate]
    outputs: List[FunctionOutputCreate]


class ImplementationFeedbackOutput(BaseModel):
    approved: bool
    feedback: Optional[str] = None

    @field_validator('feedback')
    @classmethod
    def validate_feedback_when_not_approved(cls, v, info):
        if not info.data.get('approved', True) and v is None:
            raise ValueError('Feedback is required when approved is False')
        return v


class FunctionInPipelineInfo(BaseModel):
    id: uuid.UUID
    config: Optional[dict] = None


class FinalPipelineOutput(BaseModel):
    name: str
    description: str
    functions: List[FunctionInPipelineInfo]
    periodic_schedules: List[PeriodicScheduleCreate]
    on_event_schedules: List[OnEventScheduleCreate]


# Function outputs


async def submit_detailed_function_description_output(
    _: RunContext,
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
    _: RunContext,
    result: FinalPipelineOutput
) -> FinalPipelineOutput:

    # TODO: Implement
    # This will set up a docker container with the functions and run it on some dummy data to ensure it runs
    # Raises model retry if any error

    if len(result.functions) == 0:
        raise ModelRetry("No function IDs provided!")

    return result
