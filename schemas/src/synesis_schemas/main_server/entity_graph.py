from uuid import UUID
from typing import List, Literal
from datetime import datetime
from pydantic import BaseModel, Field

from .data_sources import DATA_SOURCE_TYPE_LITERAL


# =============================================================================
# DB Models
# =============================================================================

class DataSourceFromPipelineInDB(BaseModel):
    data_source_id: UUID
    pipeline_id: UUID
    created_at: datetime
    updated_at: datetime


class DatasetFromPipelineInDB(BaseModel):
    pipeline_id: UUID
    dataset_id: UUID
    pipeline_run_id: UUID | None
    created_at: datetime
    updated_at: datetime


class DatasetFromDataSourceInDB(BaseModel):
    data_source_id: UUID
    dataset_id: UUID


class DataSourceSupportedInPipelineInDB(BaseModel):
    data_source_id: UUID
    pipeline_id: UUID
    created_at: datetime
    updated_at: datetime


class DatasetSupportedInPipelineInDB(BaseModel):
    dataset_id: UUID
    pipeline_id: UUID
    created_at: datetime
    updated_at: datetime


class ModelEntitySupportedInPipelineInDB(BaseModel):
    model_entity_id: UUID
    pipeline_id: UUID
    created_at: datetime
    updated_at: datetime


class DatasetInPipelineRunInDB(BaseModel):
    pipeline_run_id: UUID
    dataset_id: UUID
    created_at: datetime
    updated_at: datetime


class DataSourceInPipelineRunInDB(BaseModel):
    pipeline_run_id: UUID
    data_source_id: UUID
    created_at: datetime
    updated_at: datetime


class ModelEntityInPipelineRunInDB(BaseModel):
    pipeline_run_id: UUID
    model_entity_id: UUID
    created_at: datetime
    updated_at: datetime


class PipelineRunOutputDatasetInDB(BaseModel):
    pipeline_run_id: UUID
    dataset_id: UUID
    created_at: datetime
    updated_at: datetime


class PipelineRunOutputModelEntityInDB(BaseModel):
    pipeline_run_id: UUID
    model_entity_id: UUID
    created_at: datetime
    updated_at: datetime


class PipelineRunOutputDataSourceInDB(BaseModel):
    pipeline_run_id: UUID
    data_source_id: UUID
    created_at: datetime
    updated_at: datetime


class DataSourceInAnalysisInDB(BaseModel):
    id: UUID
    analysis_id: UUID
    data_source_id: UUID


class DatasetInAnalysisInDB(BaseModel):
    id: UUID
    analysis_id: UUID
    dataset_id: UUID


class ModelEntityInAnalysisInDB(BaseModel):
    id: UUID
    analysis_id: UUID
    model_entity_id: UUID


class AnalysisFromPastAnalysisInDB(BaseModel):
    id: UUID
    analysis_id: UUID
    past_analysis_id: UUID


# =============================================================================
# API Models
# =============================================================================

class EdgePoints(BaseModel):
    data_sources: List[UUID] = []
    datasets: List[UUID] = []
    analyses: List[UUID] = []
    pipelines: List[UUID] = []
    model_entities: List[UUID] = []
    pipeline_runs: List[UUID] = []


class GraphNode(BaseModel):
    id: UUID
    name: str
    description: str
    from_entities: EdgePoints
    to_entities: EdgePoints


class PipelineGraphNode(GraphNode):
    id: UUID
    name: str
    description: str
    from_entities: EdgePoints
    runs: List[GraphNode] = []


class EntityGraph(BaseModel):
    data_sources: List[GraphNode] = []
    datasets: List[GraphNode] = []
    pipelines: List[PipelineGraphNode] = []
    analyses: List[GraphNode] = []
    model_entities: List[GraphNode] = []


class EdgePointsUsingNames(BaseModel):
    data_sources: List[str] = []
    datasets: List[str] = []
    analyses: List[str] = []
    pipelines: List[str] = []
    model_entities: List[str] = []
    pipeline_runs: List[str] = []


class GraphNodeUsingNames(GraphNode):
    name: str
    description: str
    from_entities: EdgePointsUsingNames
    to_entities: EdgePointsUsingNames


class PipelineGraphNodeUsingNames(GraphNodeUsingNames):
    id: UUID
    name: str
    description: str
    from_entities: EdgePointsUsingNames
    runs: List[GraphNodeUsingNames] = []


class EntityGraphUsingNames(BaseModel):
    data_sources: List[GraphNodeUsingNames] = []
    datasets: List[GraphNodeUsingNames] = []
    pipelines: List[PipelineGraphNodeUsingNames] = []
    analyses: List[GraphNodeUsingNames] = []
    model_entities: List[GraphNodeUsingNames] = []
    pipeline_runs: List[GraphNodeUsingNames] = []


ENTITY_TYPE_LITERAL = Literal["data_source", "dataset",
                              "analysis", "pipeline", "model_entity"]


class EntityDetail(BaseModel):
    entity_id: UUID
    entity_type: ENTITY_TYPE_LITERAL
    name: str
    description: str
    inputs: EdgePoints = Field(default_factory=EdgePoints)
    outputs: EdgePoints = Field(default_factory=EdgePoints)


class EntityDetailsResponse(BaseModel):
    entity_details: List[EntityDetail]


# =============================================================================
# Create Models
# =============================================================================

class EntityEdge(BaseModel):
    from_entity_type: ENTITY_TYPE_LITERAL
    from_entity_id: UUID
    to_entity_type: ENTITY_TYPE_LITERAL
    to_entity_id: UUID
    from_pipeline_run_id: UUID | None = None
    to_pipeline_run_id: UUID | None = None


class EntityEdgesCreate(BaseModel):
    edges: List[EntityEdge] = Field(default_factory=list)
