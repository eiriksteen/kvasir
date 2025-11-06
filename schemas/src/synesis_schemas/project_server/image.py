from uuid import UUID
from pydantic import BaseModel


class GetImageRequest(BaseModel):
    """Request to get an image file from container"""
    project_id: UUID
    image_path: str

