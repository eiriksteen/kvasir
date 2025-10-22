import uuid
from pydantic import BaseModel, Field
from typing import Literal


class AnalysisResultModelResponse(BaseModel):
    analysis: str = Field(
        description="This should be a short explanation and interpretation of the result of the analysis. This should be in github flavored markdown format.")
    python_code: str = Field(
        description="The python code that was used to generate the analysis result. This code should be executable and should be able to run in a python container.")
    output_variable: str = Field(
        description="The variable that is most relevant to the analysis. This variable is likely the last variable in the code.")


class AggregationObjectCreateResponse(BaseModel):
    name: str
    description: str


class AnalysisResultMoveRequest(BaseModel):
    analysis_result_id: uuid.UUID = Field(
        description="The ID of the analysis result.")
    next_element_type: Literal['analysis_result', 'notebook_section'] = Field(
        description="The type of the next element.")
    next_element_id: uuid.UUID = Field(
        description="The ID of the next element.")
    new_section_id: uuid.UUID = Field(
        description="The ID of the new parent section.")


class SectionMoveRequest(BaseModel):
    section_id: uuid.UUID = Field(description="The ID of the section.")
    next_element_type: Literal['analysis_result', 'notebook_section'] = Field(
        description="The type of the next element.")
    next_element_id: uuid.UUID = Field(
        description="The ID of the next element.")
    new_section_id: uuid.UUID | None = Field(
        description="The ID of the new parent section (should be None if the section is to be a root section).")
