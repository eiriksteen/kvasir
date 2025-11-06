from typing import Annotated
from fastapi import APIRouter, Depends

from synesis_schemas.main_server import (
    ResultImageInDB,
    ResultImageCreate,
    User
)
from synesis_api.modules.analysis.service import create_result_image
from synesis_api.auth.service import get_current_user

router = APIRouter()


# TODO: Add security checks to verify user owns the analysis result

@router.post("/result-image", response_model=ResultImageInDB)
async def create_result_image_endpoint(
    image_create: ResultImageCreate,
    user: Annotated[User, Depends(get_current_user)] = None
) -> ResultImageInDB:
    """
    Create a new result image record.
    The image_url should point to a file in the project container.
    Use project server endpoints to fetch the actual image.
    """
    return await create_result_image(image_create)
