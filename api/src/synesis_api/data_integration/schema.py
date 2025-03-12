from pydantic import BaseModel
from datetime import datetime
from ..ontology.schema import TimeSeries, TimeSeriesDataset
from uuid import UUID


class IntegrationJobMetadata(BaseModel):
    id: UUID
    status: str
    started_at: datetime
    completed_at: datetime | None = None


class IntegrationJobMetadataInDB(IntegrationJobMetadata):
    user_id: UUID
    api_key_id: UUID


class IntegrationJobResult(BaseModel):
    job_id: UUID
    dataset_id: UUID


class IntegrationJobResultInDB(IntegrationJobResult):
    python_code: str


class DataSubmissionResponse(BaseModel):
    dataset_id: UUID


class IntegrationAgentOutput(BaseModel):
    python_code: str
    data_modality: str
    data_description: str
    dataset_name: str
    index_first_level: str
    index_second_level: str | None
    dataset_id: UUID | None = None
