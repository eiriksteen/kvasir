from synesis_api.base_schema import BaseSchema
from typing import Literal, Optional
from uuid import UUID


class Node(BaseSchema):
    id: UUID
    project_id: UUID
    x_position: int
    y_position: int


class NodeInDB(Node):
    type: Literal["data_source", "dataset", "analysis", "automation"]


class FrontendNode(BaseSchema):
    id: UUID
    project_id: UUID
    x_position: float
    y_position: float
    type: Literal["data_source", "dataset", "analysis", "automation"]
    data_source_id: Optional[UUID] = None
    dataset_id: Optional[UUID] = None
    analysis_id: Optional[UUID] = None
    automation_id: Optional[UUID] = None


class FrontendNodeCreate(BaseSchema):
    project_id: UUID
    type: Literal["data_source", "dataset", "analysis", "automation"]
    data_source_id: Optional[UUID] = None
    dataset_id: Optional[UUID] = None
    analysis_id: Optional[UUID] = None
    automation_id: Optional[UUID] = None
    x_position: Optional[float] = None
    y_position: Optional[float] = None
