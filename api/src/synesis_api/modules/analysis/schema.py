from uuid import UUID
from datetime import datetime
from typing import List, Literal
from ...base_schema import BaseSchema
from ...auth.schema import User
from pydantic_ai.messages import ModelMessage


class DelegateResult(BaseSchema):
    function_name: Literal["run_analysis_planner", "run_execution_agent", "run_simple_analysis"]

class AnalysisPlanStep(BaseSchema):
    step_name: str
    step_description: str

class AnalysisPlan(BaseSchema):
    analysis_overview: str
    analysis_plan: List[AnalysisPlanStep]


class AnalysisJobResultMetadata(BaseSchema):
    job_id: UUID
    number_of_datasets: int
    number_of_automations: int
    dataset_ids: List[UUID]
    automation_ids: List[UUID]
    analysis_plan: AnalysisPlan
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


class AnalysisJobResultMetadataList(BaseSchema):
    analyses_job_results: List[AnalysisJobResultMetadata] = []

class AnalysisRequest(BaseSchema):
    dataset_ids: List[UUID] = []
    analysis_ids: List[UUID] = []
    automation_ids: List[UUID] = []
    prompt: str | None = None
    user: User
    message_history: List[ModelMessage] = []

