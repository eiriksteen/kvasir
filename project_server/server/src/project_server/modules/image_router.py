from uuid import UUID
from typing import Annotated
from pathlib import Path
from fastapi import APIRouter, Depends, HTTPException
from fastapi.responses import Response

from project_server.auth import TokenData, decode_token
from project_server.client import ProjectClient, get_image

router = APIRouter()


@router.get("/get-image/{image_id}")
async def get_image_endpoint(
    image_id: UUID,
    token_data: Annotated[TokenData, Depends(decode_token)] = None
) -> Response:

    client = ProjectClient(bearer_token=token_data.bearer_token)
    image = await get_image(client, image_id)
    image_path = Path(image.image_path)

    allowed_extensions = ['.png', '.jpg', '.jpeg', '.gif', '.svg', '.webp']
    if image_path.suffix.lower() not in allowed_extensions:
        raise HTTPException(
            status_code=400,
            detail=f"Invalid image file type: {image_path.suffix}"
        )

    if not image_path.exists():
        raise HTTPException(
            status_code=404,
            detail=f"Image file not found: {image_path}"
        )

    try:
        with open(image_path, 'rb') as f:
            image_content = f.read()

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

        return Response(content=image_content, media_type=content_type)
    except Exception as e:
        raise HTTPException(
            status_code=500,
            detail=f"Failed to read image: {str(e)}"
        )
