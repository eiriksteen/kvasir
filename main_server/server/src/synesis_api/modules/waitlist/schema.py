from pydantic import BaseModel, Field
from datetime import datetime, timezone
from uuid import UUID


class WaitlistInDB(BaseModel):
    id: UUID
    email: str
    name: str
    affiliation: str
    role: str
    created_at: datetime = Field(
        default_factory=lambda: datetime.now(timezone.utc))


class WaitlistCreate(BaseModel):
    email: str
    name: str
    affiliation: str
    role: str
