import uuid
from pydantic import BaseModel, Field
from pydantic_ai import RunContext, ModelRetry
from typing import Literal


from project_server.agents.analysis.deps import AnalysisDeps


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


def submit_final_output(ctx: RunContext[AnalysisDeps], _: str) -> str:
    if not ctx.deps.results_generated:
        raise ModelRetry(
            "No analysis results generated! You must actually DO the analysis, NOT just create sections!")
