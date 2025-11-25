from uuid import UUID
from typing import List, Optional
from abc import ABC, abstractmethod


from kvasir_ontology.graph.data_model import (
    EntityGraph,
    EdgeDefinition,
    NodeGroupBase,
    NodeGroupCreate,
    EntityNodeCreate,
    EntityNode
)


class GraphInterface(ABC):

    def __init__(self, user_id: UUID):
        self.user_id = user_id

    @abstractmethod
    async def add_node(self, node: EntityNodeCreate) -> EntityNode:
        pass

    @abstractmethod
    async def add_nodes(self, nodes: List[EntityNodeCreate]) -> List[EntityNode]:
        pass

    @abstractmethod
    async def get_node(self, node_id: UUID) -> EntityNode:
        pass

    @abstractmethod
    async def get_nodes(self, node_ids: List[UUID]) -> List[EntityNode]:
        pass

    @abstractmethod
    async def delete_node(self, node_id: UUID) -> None:
        pass

    @abstractmethod
    async def update_node_position(self, node_id: UUID, x_position: float, y_position: float) -> EntityNode:
        pass

    @abstractmethod
    async def get_node_edges(self, node_id: UUID) -> List[EdgeDefinition]:
        pass

    @abstractmethod
    async def get_node_groups(self, node_id: Optional[UUID] = None, group_ids: Optional[List[UUID]] = None) -> List[NodeGroupBase]:
        pass

    @abstractmethod
    async def get_node_group(self, node_group_id: UUID) -> NodeGroupBase:
        pass

    @abstractmethod
    async def create_node_group(self, node_group: NodeGroupCreate) -> NodeGroupBase:
        pass

    @abstractmethod
    async def delete_node_group(self, node_group_id: UUID) -> None:
        pass

    @abstractmethod
    async def add_node_to_group(self, node_id: UUID, node_group_id: UUID) -> None:
        pass

    @abstractmethod
    async def remove_nodes_from_groups(self, node_ids: List[UUID], node_group_ids: List[UUID]) -> None:
        pass

    @abstractmethod
    async def create_edges(self, edges: List[EdgeDefinition]) -> None:
        pass

    @abstractmethod
    async def remove_edges(self, edges: List[EdgeDefinition]) -> None:
        pass

    @abstractmethod
    async def remove_pipeline_run_edges(self, pipeline_run_ids: List[UUID]) -> None:
        pass

    @abstractmethod
    async def get_entity_graph(
            self,
            root_group_id: Optional[UUID] = None,
            root_node_id: Optional[UUID] = None) -> EntityGraph:
        # One of root_group_id or root_node_id must be provided
        pass
