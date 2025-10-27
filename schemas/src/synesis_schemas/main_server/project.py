from datetime import datetime, timezone
from typing import List, Literal
from uuid import UUID
from pydantic import model_validator
from pydantic import BaseModel

from .data_sources import DATA_SOURCE_TYPE_LITERAL

# DB Schemas


ENTITY_TYPE_LITERAL = Literal["data_source", "dataset",
                              "analysis", "pipeline", "model_entity"]


class ProjectInDB(BaseModel):
    id: UUID
    user_id: UUID
    name: str
    description: str
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
    model_entity_id: UUID
    x_position: float
    y_position: float
    created_at: datetime = datetime.now(timezone.utc)
    updated_at: datetime = datetime.now(timezone.utc)


#


class ProjectCreate(BaseModel):
    name: str
    description: str


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


class GraphNodeConnections(BaseModel):
    from_data_sources: List[UUID] = []
    from_datasets: List[UUID] = []
    from_analyses: List[UUID] = []
    from_pipelines: List[UUID] = []
    from_model_entities: List[UUID] = []
    to_datasets: List[UUID] = []
    to_analyses: List[UUID] = []
    to_pipelines: List[UUID] = []
    to_model_entities: List[UUID] = []


class DataSourceInGraph(BaseModel):
    id: UUID
    name: str
    type: DATA_SOURCE_TYPE_LITERAL
    brief_description: str
    x_position: float
    y_position: float
    connections: GraphNodeConnections


class DatasetInGraph(BaseModel):
    id: UUID
    name: str
    brief_description: str
    x_position: float
    y_position: float
    connections: GraphNodeConnections


class PipelineInGraph(BaseModel):
    id: UUID
    name: str
    brief_description: str
    x_position: float
    y_position: float
    connections: GraphNodeConnections


class AnalysisInGraph(BaseModel):
    id: UUID
    name: str
    x_position: float
    y_position: float
    brief_description: str
    connections: GraphNodeConnections


class ModelEntityInGraph(BaseModel):
    id: UUID
    name: str
    x_position: float
    y_position: float
    brief_description: str
    connections: GraphNodeConnections


class ProjectGraph(BaseModel):
    data_sources: List[DataSourceInGraph] = []
    datasets: List[DatasetInGraph] = []
    pipelines: List[PipelineInGraph] = []
    analyses: List[AnalysisInGraph] = []
    model_entities: List[ModelEntityInGraph] = []


class Project(BaseModel):
    id: UUID
    user_id: UUID
    name: str
    description: str
    data_sources: List[ProjectDataSourceInDB] = []
    datasets: List[ProjectDatasetInDB] = []
    analyses: List[ProjectAnalysisInDB] = []
    pipelines: List[ProjectPipelineInDB] = []
    model_entities: List[ProjectModelEntityInDB] = []
    view_port_x: float = 0.0
    view_port_y: float = 0.0
    view_port_zoom: float = 1.0
    created_at: datetime = datetime.now(timezone.utc)
    updated_at: datetime = datetime.now(timezone.utc)
