from fastapi import APIRouter, Depends, Query
from typing import List, Annotated, Optional
from uuid import UUID

from kvasir_ontology.graph.interface import GraphInterface
from kvasir_ontology.graph.data_model import (
    LeafNode,
    LeafNodeCreate,
    EdgeCreate,
    BranchNodeBase,
    BranchNodeCreate,
    EntityGraph,
)
from kvasir_api.modules.entity_graph.service import get_graph_service


router = APIRouter()


@router.get("/node/{node_id}", response_model=LeafNode)
async def get_node(
    node_id: UUID,
    graph_service: Annotated[GraphInterface, Depends(get_graph_service)]
) -> LeafNode:
    return await graph_service.get_node(node_id)


@router.get("/leaf-node/entity/{entity_id}", response_model=LeafNode)
async def get_leaf_node_by_entity_id(
    entity_id: UUID,
    graph_service: Annotated[GraphInterface, Depends(get_graph_service)]
) -> LeafNode:
    return await graph_service.get_leaf_node_by_entity_id(entity_id)


@router.put("/node/{node_id}/position")
async def update_node_position(
    node_id: UUID,
    x_position: float,
    y_position: float,
    graph_service: Annotated[GraphInterface, Depends(get_graph_service)]
) -> dict:
    await graph_service.update_node_position(node_id, x_position, y_position)
    return {"message": "Node position updated successfully"}


@router.delete("/node/{node_id}")
async def delete_node(
    node_id: UUID,
    graph_service: Annotated[GraphInterface, Depends(get_graph_service)]
) -> None:
    await graph_service.delete_nodes(node_id)


@router.post("/edges")
async def create_edges(
    edges: List[EdgeCreate],
    graph_service: Annotated[GraphInterface, Depends(get_graph_service)]
) -> None:
    await graph_service.create_edges(edges)


@router.delete("/edges")
async def remove_edges(
    edges: List[EdgeCreate],
    graph_service: Annotated[GraphInterface, Depends(get_graph_service)]
) -> None:
    await graph_service.remove_edges(edges)


@router.get("/entity-graph/{root_node_id}", response_model=EntityGraph)
async def get_entity_graph(
    graph_service: Annotated[GraphInterface, Depends(get_graph_service)],
    root_node_id: UUID,
) -> EntityGraph:
    entity_graph_obj = await graph_service.get_entity_graph(root_node_id=root_node_id)
    return entity_graph_obj
