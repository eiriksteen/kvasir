from datetime import datetime, timezone
from uuid import UUID
from typing import Literal, Optional
from synesis_api.base_schema import BaseSchema


class Job(BaseSchema):
    id: UUID
    type: str
    status: Literal["pending",
                    "running",
                    "completed",
                    "failed",
                    "paused",
                    "awaiting_approval"]
    conversation_id: Optional[UUID] = None
    job_name: Optional[str] = None
    started_at: datetime = datetime.now(timezone.utc)
    completed_at: Optional[datetime] = None


class JobInDB(Job):
    user_id: UUID
