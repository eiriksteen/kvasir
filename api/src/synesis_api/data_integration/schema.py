from datetime import datetime
from uuid import UUID
from ..base_schema import BaseSchema


class IntegrationJobMetadata(BaseSchema):
    id: UUID
    status: str
    started_at: datetime
    completed_at: datetime | None = None


class IntegrationJobMetadataInDB(IntegrationJobMetadata):
    user_id: UUID
    api_key_id: UUID


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
