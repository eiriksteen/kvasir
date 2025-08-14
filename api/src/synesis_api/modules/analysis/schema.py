from uuid import UUID
from datetime import datetime
from typing import List, Literal
from synesis_api.base_schema import BaseSchema
from datetime import timezone


class AnalysisPlanStep(BaseSchema):
    step_name: str
    step_description: str


class AnalysisPlan(BaseSchema):
    analysis_overview: str
    analysis_plan: List[AnalysisPlanStep]


class AnalysisStatusMessage(BaseSchema):
    id: UUID
    job_id: UUID
    type: Literal["tool_call", "tool_result", "analysis_result", "user_prompt"]
    message: str
    created_at: datetime = datetime.now(timezone.utc)


class AnalysisJobResultMetadata(BaseSchema):
    job_id: UUID
    name: str
    number_of_datasets: int
    number_of_automations: int
    dataset_ids: List[UUID]
    automation_ids: List[UUID]
    analysis_plan: AnalysisPlan
    status_messages: List[AnalysisStatusMessage]
    created_at: datetime
    pdf_created: bool


class AnalysisJobResultMetadataInDB(AnalysisJobResultMetadata):
    pdf_s3_path: str | None = None
    user_id: UUID


class AnalysisJobResult(BaseSchema):
    analysis: str | None = None
    python_code: str | None = None


class AnalysisJobResultInDB(AnalysisJobResult):
    pass
