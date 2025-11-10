from fastapi import APIRouter, Depends, Query
from typing import List
from uuid import UUID

from synesis_schemas.main_server import (
    EdgesCreate,
    EntityDetailsResponse,
    User,
)
from synesis_api.modules.entity_graph.service import (
    create_edges,
    remove_edges,
    get_entity_details,
)
from synesis_api.auth.service import get_current_user

router = APIRouter()


@router.post("/edges")
async def add_edges(edges: EdgesCreate) -> str:
    """
    Add one or more edges between entities in the entity graph.
    """
    await create_edges(edges)
    return "Edges created successfully"


@router.delete("/edges")
async def delete_edges(edges: EdgesCreate) -> str:
    """
    Remove one or more edges between entities in the entity graph.
    """
    await remove_edges(edges)
    return "Edges removed successfully"


@router.get("/entity-details")
async def get_entity_details_endpoint(
    entity_ids: List[UUID] = Query(...),
    user: User = Depends(get_current_user)
) -> EntityDetailsResponse:
    """
    Get detailed information about entities including their inputs and outputs.
    This provides comprehensive descriptions that include the entity's connections in the graph.
    """
    return await get_entity_details(user.id, entity_ids)
