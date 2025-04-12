from uuid import UUID
from ...base_schema import BaseSchema


class IntegrationJobResult(BaseSchema):
    job_id: UUID
    dataset_id: UUID


class IntegrationJobResultInDB(IntegrationJobResult):
    python_code: str


class DataSubmissionResponse(BaseSchema):
    dataset_id: UUID


class IntegrationAgentOutput(BaseSchema):
    python_code: str
    data_modality: str
    data_description: str
    dataset_name: str
    index_first_level: str
    index_second_level: str | None
    dataset_id: UUID | None = None


class IntegrationAgentState(BaseSchema):
    agent_state: str
