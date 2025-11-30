from typing import Annotated
from uuid import UUID
from fastapi import APIRouter, Depends

from kvasir_api.modules.codebase.service import Codebase, get_codebase_service
from kvasir_ontology.code.data_model import CodebasePath, CodebaseFile, CodebaseFilePaginated


router = APIRouter()


@router.get("/{mount_node_id}/tree", response_model=CodebasePath)
async def get_codebase_tree_endpoint(
    mount_node_id: UUID,
    codebase_service: Annotated[Codebase, Depends(get_codebase_service)]
) -> CodebasePath:
    """Get the full codebase tree structure for a project."""
    return await codebase_service.get_codebase_tree()


@router.get("/{mount_node_id}/file", response_model=CodebaseFile)
async def get_codebase_file_endpoint(
    mount_node_id: UUID,
    file_path: str,
    codebase_service: Annotated[Codebase, Depends(get_codebase_service)]
) -> CodebaseFile:
    """Get the content of a specific file in the codebase."""
    return await codebase_service.get_codebase_file(file_path)


@router.get("/{mount_node_id}/file/paginated", response_model=CodebaseFilePaginated)
async def get_codebase_file_paginated_endpoint(
    mount_node_id: UUID,
    file_path: str,
    codebase_service: Annotated[Codebase, Depends(get_codebase_service)],
    offset: int = 0,
    limit: int = 100
) -> CodebaseFilePaginated:
    """Get a paginated portion of a file's content.

    Args:
        mount_node_id: The mount node ID
        file_path: Path to the file
        offset: Line number to start from (0-indexed)
        limit: Number of lines to return (default: 100)
    """
    return await codebase_service.get_codebase_file_paginated(file_path, offset, limit)
