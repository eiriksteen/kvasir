from fastapi import APIRouter, Depends, Query
from typing import List, Annotated, Optional
from uuid import UUID

from kvasir_ontology.graph.interface import GraphInterface
from kvasir_ontology.graph.data_model import (
    EntityNode,
    EntityNodeCreate,
    EdgeDefinition,
    NodeGroupBase,
    NodeGroupCreate,
    EntityGraph,
)
from synesis_api.modules.entity_graph.service import get_graph_service


router = APIRouter()


@router.post("/node", response_model=EntityNode)
async def add_node(
    node: EntityNodeCreate,
    graph_service: Annotated[GraphInterface, Depends(get_graph_service)]
) -> EntityNode:
    return await graph_service.add_node(node)


@router.get("/node/{node_id}", response_model=EntityNode)
async def get_node(
    node_id: UUID,
    graph_service: Annotated[GraphInterface, Depends(get_graph_service)]
) -> EntityNode:
    return await graph_service.get_node(node_id)


@router.put("/node/{node_id}/position", response_model=EntityNode)
async def update_node_position(
    node_id: UUID,
    x_position: float,
    y_position: float,
    graph_service: Annotated[GraphInterface, Depends(get_graph_service)]
) -> EntityNode:
    return await graph_service.update_node_position(node_id, x_position, y_position)


@router.delete("/node/{node_id}")
async def delete_node(
    node_id: UUID,
    graph_service: Annotated[GraphInterface, Depends(get_graph_service)]
) -> None:
    await graph_service.delete_node(node_id)


@router.get("/node/{node_id}/edges", response_model=List[EdgeDefinition])
async def get_node_edges(
    node_id: UUID,
    graph_service: Annotated[GraphInterface, Depends(get_graph_service)]
) -> List[EdgeDefinition]:
    return await graph_service.get_node_edges(node_id)


@router.get("/node/{node_id}/groups", response_model=List[NodeGroupBase])
async def get_node_groups_by_node(
    node_id: UUID,
    graph_service: Annotated[GraphInterface, Depends(get_graph_service)]
) -> List[NodeGroupBase]:
    return await graph_service.get_node_groups(node_id=node_id)


@router.get("/node-groups", response_model=List[NodeGroupBase])
async def get_node_groups(
    graph_service: Annotated[GraphInterface, Depends(get_graph_service)],
    node_id: Optional[UUID] = Query(None),
    group_ids: Optional[List[UUID]] = Query(None),
) -> List[NodeGroupBase]:
    return await graph_service.get_node_groups(node_id=node_id, group_ids=group_ids)


@router.post("/node-group", response_model=NodeGroupBase)
async def create_node_group(
    node_group: NodeGroupCreate,
    graph_service: Annotated[GraphInterface, Depends(get_graph_service)]
) -> NodeGroupBase:
    return await graph_service.create_node_group(node_group)


@router.delete("/node-group/{node_group_id}")
async def delete_node_group(
    node_group_id: UUID,
    graph_service: Annotated[GraphInterface, Depends(get_graph_service)]
) -> None:
    await graph_service.delete_node_group(node_group_id)


@router.post("/node/{node_id}/group/{node_group_id}")
async def add_node_to_group(
    node_id: UUID,
    node_group_id: UUID,
    graph_service: Annotated[GraphInterface, Depends(get_graph_service)]
) -> None:
    await graph_service.add_node_to_group(node_id, node_group_id)


@router.delete("/nodes/groups")
async def remove_nodes_from_groups(
    graph_service: Annotated[GraphInterface, Depends(get_graph_service)],
    node_ids: List[UUID] = Query(...),
    node_group_ids: List[UUID] = Query(...),
) -> None:
    await graph_service.remove_nodes_from_groups(node_ids, node_group_ids)


@router.post("/edges")
async def create_edges(
    edges: List[EdgeDefinition],
    graph_service: Annotated[GraphInterface, Depends(get_graph_service)]
) -> None:
    await graph_service.create_edges(edges)


@router.delete("/edges")
async def remove_edges(
    edges: List[EdgeDefinition],
    graph_service: Annotated[GraphInterface, Depends(get_graph_service)]
) -> None:
    await graph_service.remove_edges(edges)


@router.get("/entity-graph", response_model=EntityGraph)
async def get_entity_graph(
    graph_service: Annotated[GraphInterface, Depends(get_graph_service)],
    root_group_id: Optional[UUID] = Query(None),
    root_node_id: Optional[UUID] = Query(None),
) -> EntityGraph:
    return await graph_service.get_entity_graph(
        root_group_id=root_group_id,
        root_node_id=root_node_id
    )
