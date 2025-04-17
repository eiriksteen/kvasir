from uuid import UUID
from ...base_schema import BaseSchema


class IntegrationJobResult(BaseSchema):
    job_id: UUID
    dataset_id: UUID


class IntegrationJobResultInDB(IntegrationJobResult):
    python_code: str


class DataSubmissionResponse(BaseSchema):
    dataset_id: UUID


class IntegrationAgentState(BaseSchema):
    agent_state: str
