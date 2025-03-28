from datetime import datetime
from uuid import UUID
from ..base_schema import BaseSchema


class JobMetadata(BaseSchema):
    id: UUID
    type: str
    status: str
    started_at: datetime
    completed_at: datetime | None = None


class IntegrationJobMetadataInDB(JobMetadata):
    user_id: UUID
    api_key_id: UUID
