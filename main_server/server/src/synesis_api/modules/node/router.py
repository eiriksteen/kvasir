from typing import List
from uuid import UUID
from fastapi import APIRouter, Depends, HTTPException

from synesis_schemas.main_server import User
from synesis_api.auth.service import get_current_user
from synesis_schemas.main_server import FrontendNode, FrontendNodeCreate
from synesis_api.modules.node.service import (
    create_node,
    get_node,
    get_project_nodes,
    update_node_position,
    delete_node,
)
from synesis_api.auth.service import user_owns_project


router = APIRouter()


@router.post("/create-node", response_model=FrontendNode)
async def create_new_node(
    node: FrontendNodeCreate,
    user: User = Depends(get_current_user)
) -> FrontendNode:
    # Verify project exists and user has access

    if not await user_owns_project(user.id, node.project_id):
        raise HTTPException(
            status_code=403, detail="Not authorized to access this project")

    try:
        created_node = await create_node(node)
        return created_node
    except Exception as e:
        raise HTTPException(
            status_code=500, detail=f"Could not create node: {str(e)}")


@router.get("/project/{project_id}", response_model=List[FrontendNode])
async def get_nodes_by_project(
    project_id: UUID,
    user: User = Depends(get_current_user)
) -> List[FrontendNode]:
    # Verify project exists and user has access
    if not await user_owns_project(user.id, project_id):
        raise HTTPException(
            status_code=403, detail="Not authorized to access this project")

    return await get_project_nodes(project_id)


@router.put("/update-node/{node_id}", response_model=FrontendNode)
async def update_node_position_endpoint(
    node: FrontendNode,
    user: User = Depends(get_current_user)
) -> FrontendNode:
    # First get the node to check permissions
    check_node = await get_node(node.id)
    if not check_node:
        raise HTTPException(status_code=404, detail="Node not found")

    # Verify user has access to the project
    if not await user_owns_project(user.id, node.project_id):
        raise HTTPException(
            status_code=403, detail="Not authorized to update this node")

    updated_node = await update_node_position(node)
    if not updated_node:
        raise HTTPException(
            status_code=404, detail="Could not update node position")

    return updated_node


@router.delete("/delete/{node_id}", response_model=UUID)
async def delete_node_endpoint(
    node_id: UUID,
    user: User = Depends(get_current_user)
) -> UUID:

    check_node = await get_node(node_id)
    if not check_node:
        raise HTTPException(status_code=404, detail="Node not found")

    if not await user_owns_project(user.id, check_node.project_id):
        raise HTTPException(
            status_code=403, detail="Not authorized to delete this node")

    await delete_node(node_id)

    return node_id
