from datetime import datetime, timezone
from typing import List, Literal, Optional, TYPE_CHECKING
from uuid import UUID
from pydantic import model_validator
from pydantic import BaseModel

from kvasir_ontology.main_server.entity_graph import EntityGraph

# DB Schemas


ENTITY_TYPE_LITERAL = Literal["data_source", "dataset",
                              "analysis", "pipeline", "model_instantiated"]


class ProjectInDB(BaseModel):
    id: UUID
    user_id: UUID
    name: str
    description: str
    python_package_name: str
    view_port_x: float = 0.0
    view_port_y: float = 0.0
    view_port_zoom: float = 1.0
    created_at: datetime = datetime.now(timezone.utc)
    updated_at: datetime = datetime.now(timezone.utc)


class ProjectDataSourceInDB(BaseModel):
    project_id: UUID
    data_source_id: UUID
    x_position: float
    y_position: float
    created_at: datetime = datetime.now(timezone.utc)
    updated_at: datetime = datetime.now(timezone.utc)


class ProjectDatasetInDB(BaseModel):
    project_id: UUID
    dataset_id: UUID
    x_position: float
    y_position: float
    created_at: datetime = datetime.now(timezone.utc)
    updated_at: datetime = datetime.now(timezone.utc)


class ProjectAnalysisInDB(BaseModel):
    project_id: UUID
    analysis_id: UUID
    x_position: float
    y_position: float
    created_at: datetime = datetime.now(timezone.utc)
    updated_at: datetime = datetime.now(timezone.utc)


class ProjectPipelineInDB(BaseModel):
    project_id: UUID
    pipeline_id: UUID
    x_position: float
    y_position: float
    created_at: datetime = datetime.now(timezone.utc)
    updated_at: datetime = datetime.now(timezone.utc)


class ProjectModelEntityInDB(BaseModel):
    project_id: UUID
    model_instantiated_id: UUID
    x_position: float
    y_position: float
    created_at: datetime = datetime.now(timezone.utc)
    updated_at: datetime = datetime.now(timezone.utc)


#


class ProjectCreate(BaseModel):
    name: str
    description: str
    python_package_name: Optional[str] = None


class ProjectDetailsUpdate(BaseModel):
    project_id: UUID
    name: str | None = None
    description: str | None = None

    @model_validator(mode='after')
    def validate_at_least_one_field_provided(self):
        if self.name is None and self.description is None:
            raise ValueError(
                "At least one field (name or description) must be provided")
        return self


class EntityPositionCreate(BaseModel):
    x: float
    y: float


class AddEntityToProject(BaseModel):
    project_id: UUID
    entity_type: ENTITY_TYPE_LITERAL
    entity_id: UUID


class RemoveEntityFromProject(BaseModel):
    project_id: UUID
    entity_type: ENTITY_TYPE_LITERAL
    entity_id: UUID


class UpdateEntityPosition(BaseModel):
    project_id: UUID
    entity_type: ENTITY_TYPE_LITERAL
    entity_id: UUID
    x_position: float
    y_position: float


class UpdateProjectViewport(BaseModel):
    project_id: UUID
    x: float
    y: float
    zoom: float


class ProjectNodes(BaseModel):
    project_data_sources: List[ProjectDataSourceInDB] = []
    project_datasets: List[ProjectDatasetInDB] = []
    project_pipelines: List[ProjectPipelineInDB] = []
    project_analyses: List[ProjectAnalysisInDB] = []
    project_model_entities: List[ProjectModelEntityInDB] = []


class Project(ProjectInDB):
    graph: EntityGraph
    project_nodes: ProjectNodes
