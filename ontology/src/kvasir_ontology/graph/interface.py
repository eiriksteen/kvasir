from uuid import UUID
from typing import List, Optional, Union
from abc import ABC, abstractmethod


from kvasir_ontology.graph.data_model import (
    EntityGraph,
    EdgeCreate,
    BranchNodeCreate,
    LeafNodeCreate,
    LeafNode,
    BranchNode,
    PipelineNode
)


class GraphInterface(ABC):

    def __init__(self, user_id: UUID):
        self.user_id = user_id

    @abstractmethod
    async def add_nodes(self, nodes: List[Union[LeafNodeCreate, BranchNodeCreate]]) -> List[UUID]:
        pass

    @abstractmethod
    async def get_node(self, node_id: UUID) -> Union[LeafNode, BranchNode]:
        pass

    @abstractmethod
    async def get_leaf_node_by_entity_id(self, entity_id: UUID) -> Union[LeafNode, PipelineNode]:
        pass

    @abstractmethod
    async def delete_nodes(
        self,
        node_ids: Optional[List[UUID]] = None,
        entity_ids: Optional[List[UUID]] = None
    ) -> None:
        pass

    @abstractmethod
    async def update_node_position(self, node_id: UUID, x_position: float, y_position: float) -> None:
        pass

    @abstractmethod
    async def add_node_parents(self, child_ids: List[UUID], parent_ids: List[UUID]) -> None:
        pass

    @abstractmethod
    async def remove_node_parents(self, child_ids: List[UUID], parent_ids: List[UUID]) -> None:
        pass

    @abstractmethod
    async def create_edges(self, edges: List[EdgeCreate]) -> None:
        pass

    @abstractmethod
    async def remove_entity_edges(self, entity_id: UUID):
        pass

    @abstractmethod
    async def remove_edges(self, from_entities: List[UUID], to_entities: List[UUID]) -> None:
        pass

    @abstractmethod
    async def get_entity_graph(self, root_node_id: UUID) -> EntityGraph:
        pass

    @abstractmethod
    async def get_node_leaves(self, node_id: UUID) -> List[LeafNode]:
        pass
