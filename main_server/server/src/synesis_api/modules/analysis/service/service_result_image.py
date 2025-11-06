import uuid
from typing import List
from sqlalchemy import select, insert, delete
from fastapi import HTTPException

from synesis_api.database.service import execute, fetch_one, fetch_all
from synesis_api.modules.analysis.models import result_image
from synesis_schemas.main_server import ResultImageInDB, ResultImageCreate


async def create_result_image(image_create: ResultImageCreate) -> ResultImageInDB:
    """Create a new result image record."""
    image_id = uuid.uuid4()
    image_in_db = ResultImageInDB(
        id=image_id,
        **image_create.model_dump()
    )
    await execute(
        insert(result_image).values(**image_in_db.model_dump()),
        commit_after=True
    )

    return image_in_db


async def get_result_images_by_analysis_result_id(analysis_result_id: uuid.UUID) -> List[ResultImageInDB]:
    """Get all result images for a specific analysis result."""
    results = await fetch_all(
        select(result_image).where(
            result_image.c.analysis_result_id == analysis_result_id)
    )

    return [ResultImageInDB(**result) for result in results]


async def delete_result_image(image_id: uuid.UUID) -> bool:
    """Delete a result image by ID."""
    image_id = select(result_image.c.id).where(result_image.c.id == image_id)

    if not image_id:
        return False

    await execute(
        delete(result_image).where(result_image.c.id == image_id),
        commit_after=True
    )

    return True
