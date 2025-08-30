from datetime import datetime, timezone
from typing import List, Literal
from uuid import UUID
from pydantic import model_validator
from synesis_api.base_schema import BaseSchema


class Project(BaseSchema):
    id: UUID
    user_id: UUID
    name: str
    description: str
    created_at: datetime = datetime.now(timezone.utc)
    updated_at: datetime = datetime.now(timezone.utc)
    data_source_ids: List[UUID] = []
    dataset_ids: List[UUID] = []
    analysis_ids: List[UUID] = []
    pipeline_ids: List[UUID] = []


class ProjectCreate(BaseSchema):
    name: str
    description: str


class ProjectDetailsUpdate(BaseSchema):
    name: str | None = None
    description: str | None = None

    @model_validator(mode='after')
    def validate_at_least_one_field_provided(self):
        if self.name is None and self.description is None:
            raise ValueError(
                "At least one field (name or description) must be provided")
        return self


class AddEntityToProject(BaseSchema):
    entity_type: Literal["data_source", "dataset", "analysis", "pipeline"]
    entity_id: UUID


class RemoveEntityFromProject(BaseSchema):
    entity_type: Literal["data_source", "dataset", "analysis", "pipeline"]
    entity_id: UUID
