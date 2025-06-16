from datetime import datetime, timezone
from typing import List, Literal
from uuid import UUID
from synesis_api.base_schema import BaseSchema


class Project(BaseSchema):
    id: UUID
    user_id: UUID
    name: str
    description: str
    created_at: datetime = datetime.now(timezone.utc)
    updated_at: datetime = datetime.now(timezone.utc)
    dataset_ids: List[UUID] = []
    analysis_ids: List[UUID] = []
    automation_ids: List[UUID] = []


class ProjectCreate(BaseSchema):
    name: str
    description: str


class ProjectUpdate(BaseSchema):
    name: str | None = None
    description: str | None = None
    type: Literal["dataset", "analysis", "automation"] | None = None
    id: UUID | None = None
    remove: bool | None = None
