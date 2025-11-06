from typing import Annotated
from pathlib import Path
from fastapi import APIRouter, Depends, HTTPException
from fastapi.responses import Response

from project_server.auth import TokenData, decode_token
from project_server.client import ProjectClient, get_project
from project_server.utils.docker_utils import (
    read_file_from_container,
    check_file_exists_in_container,
    create_project_container_if_not_exists
)
from synesis_schemas.project_server import GetImageRequest

router = APIRouter()


@router.post("/get-image")
async def get_image(
    request: GetImageRequest,
    token_data: Annotated[TokenData, Depends(decode_token)] = None
) -> Response:

    client = ProjectClient(bearer_token=token_data.bearer_token)
    project = await get_project(client, request.project_id)
    await create_project_container_if_not_exists(project)
    container_name = str(request.project_id)

    image_path = Path(request.image_path)

    exists = await check_file_exists_in_container(image_path, container_name)
    if not exists:
        raise HTTPException(
            status_code=404,
            detail=f"Image file not found: {request.image_path}"
        )

    allowed_extensions = ['.png', '.jpg', '.jpeg', '.gif', '.svg', '.webp']
    if image_path.suffix.lower() not in allowed_extensions:
        raise HTTPException(
            status_code=400,
            detail=f"Invalid image file type: {image_path.suffix}"
        )

    try:
        image_content = await read_file_from_container(image_path, container_name)

        content_type_map = {
            '.png': 'image/png',
            '.jpg': 'image/jpeg',
            '.jpeg': 'image/jpeg',
            '.gif': 'image/gif',
            '.svg': 'image/svg+xml',
            '.webp': 'image/webp'
        }
        content_type = content_type_map.get(
            image_path.suffix.lower(), 'application/octet-stream')

        return Response(content=image_content.encode() if isinstance(image_content, str) else image_content, media_type=content_type)
    except Exception as e:
        raise HTTPException(
            status_code=500,
            detail=f"Failed to read image from container: {str(e)}"
        )
