from pydantic import BaseModel
from typing import Literal, Optional
from uuid import UUID


class Node(BaseModel):
    id: UUID
    project_id: UUID
    x_position: int
    y_position: int


class NodeInDB(Node):
    type: Literal["data_source", "dataset",
                  "analysis", "pipeline", "model_entity"]


class FrontendNode(BaseModel):
    id: UUID
    project_id: UUID
    x_position: float
    y_position: float
    type: Literal["data_source", "dataset",
                  "analysis", "pipeline", "model_entity"]
    data_source_id: Optional[UUID] = None
    dataset_id: Optional[UUID] = None
    analysis_id: Optional[UUID] = None
    pipeline_id: Optional[UUID] = None
    model_entity_id: Optional[UUID] = None


class FrontendNodeCreate(BaseModel):
    project_id: UUID
    type: Literal["data_source", "dataset",
                  "analysis", "pipeline", "model_entity"]
    data_source_id: Optional[UUID] = None
    dataset_id: Optional[UUID] = None
    analysis_id: Optional[UUID] = None
    pipeline_id: Optional[UUID] = None
    model_entity_id: Optional[UUID] = None
    x_position: Optional[float] = None
    y_position: Optional[float] = None
