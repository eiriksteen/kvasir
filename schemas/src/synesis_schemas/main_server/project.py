from datetime import datetime, timezone
from typing import List, Literal
from uuid import UUID
from pydantic import model_validator
from pydantic import BaseModel


class Project(BaseModel):
    id: UUID
    user_id: UUID
    name: str
    description: str
    created_at: datetime = datetime.now(timezone.utc)
    updated_at: datetime = datetime.now(timezone.utc)
    data_source_ids: List[UUID] = []
    model_source_ids: List[UUID] = []
    dataset_ids: List[UUID] = []
    analysis_ids: List[UUID] = []
    pipeline_ids: List[UUID] = []
    model_ids: List[UUID] = []


class ProjectCreate(BaseModel):
    name: str
    description: str


class ProjectDetailsUpdate(BaseModel):
    name: str | None = None
    description: str | None = None

    @model_validator(mode='after')
    def validate_at_least_one_field_provided(self):
        if self.name is None and self.description is None:
            raise ValueError(
                "At least one field (name or description) must be provided")
        return self


class AddEntityToProject(BaseModel):
    project_id: UUID
    entity_type: Literal["data_source", "model_source", "dataset",
                         "analysis", "pipeline", "model"]
    entity_id: UUID


class RemoveEntityFromProject(BaseModel):
    project_id: UUID
    entity_type: Literal["data_source", "model_source", "dataset",
                         "analysis", "pipeline", "model"]
    entity_id: UUID
