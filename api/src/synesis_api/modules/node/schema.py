from synesis_api.base_schema import BaseSchema
from typing import Literal
from uuid import UUID, uuid4


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
    data_source_id: UUID | None
    dataset_id: UUID | None
    analysis_id: UUID | None
    automation_id: UUID | None


class FrontendNodeCreate(BaseSchema):
    project_id: UUID
    x_position: float
    y_position: float
    type: Literal["data_source", "dataset", "analysis", "automation"]
    data_source_id: UUID | None
    dataset_id: UUID | None
    analysis_id: UUID | None
    automation_id: UUID | None
