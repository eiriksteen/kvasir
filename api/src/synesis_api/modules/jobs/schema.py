from datetime import datetime, timezone
from uuid import UUID
from typing import Literal, List
from synesis_api.base_schema import BaseSchema


class JobMetadata(BaseSchema):
    id: UUID
    type: str
    status: Literal["pending",
                    "running",
                    "completed",
                    "failed",
                    "paused",
                    "awaiting_approval"]
    job_name: str | None = None
    started_at: datetime = datetime.now(timezone.utc)
    completed_at: datetime | None = None


class JobMetadataInDB(JobMetadata):
    user_id: UUID
