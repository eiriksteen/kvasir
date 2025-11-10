from uuid import UUID
from typing import Annotated, List
from fastapi import APIRouter, Depends

from synesis_schemas.main_server import (
    ImageCreate,
    ImageInDB,
    EchartCreate,
    EchartInDB,
    TableCreate,
    TableInDB,
    User,
)
from synesis_api.auth.service import get_current_user
from synesis_api.modules.visualization.service import (
    create_images,
    create_echarts,
    create_tables,
    get_images,
    get_echarts,
    get_tables,
)


router = APIRouter()


@router.get("/images/{image_id}", response_model=ImageInDB)
async def get_image_endpoint(
    image_id: UUID,
    _: Annotated[User, Depends(get_current_user)] = None
) -> ImageInDB:
    """Get an image"""
    return (await get_images([image_id]))[0]


@router.post("/images", response_model=List[ImageInDB])
async def post_images_endpoint(
    image_creates: List[ImageCreate],
    _: Annotated[User, Depends(get_current_user)] = None
) -> List[ImageInDB]:
    """Create new images"""
    return await create_images(image_creates)


@router.get("/echarts/{echart_id}", response_model=EchartInDB)
async def get_echart_endpoint(
    echart_id: UUID,
    _: Annotated[User, Depends(get_current_user)] = None
) -> EchartInDB:
    """Get an echart"""
    return (await get_echarts([echart_id]))[0]


@router.post("/echarts", response_model=List[EchartInDB])
async def post_echarts_endpoint(
    echart_creates: List[EchartCreate],
    _: Annotated[User, Depends(get_current_user)] = None
) -> List[EchartInDB]:
    """Create new echarts"""
    return await create_echarts(echart_creates)


@router.get("/tables/{table_id}", response_model=TableInDB)
async def get_table_endpoint(
    table_id: UUID,
    _: Annotated[User, Depends(get_current_user)] = None
) -> TableInDB:
    """Get a table"""
    return (await get_tables([table_id]))[0]


@router.post("/tables", response_model=List[TableInDB])
async def post_tables_endpoint(
    table_creates: List[TableCreate],
    _: Annotated[User, Depends(get_current_user)] = None
) -> List[TableInDB]:
    """Create new tables"""
    return await create_tables(table_creates)
