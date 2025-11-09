import uuid
from datetime import datetime, timezone
from typing import List
from sqlalchemy import insert, select

from synesis_api.database.service import execute, fetch_all
from synesis_api.modules.visualization.models import image, echart, table
from synesis_schemas.main_server import (
    ImageInDB, ImageCreate,
    EchartInDB, EchartCreate,
    TableInDB, TableCreate
)


async def create_images(image_creates: List[ImageCreate]) -> List[ImageInDB]:
    images_in_db = [ImageInDB(
        id=uuid.uuid4(),
        created_at=datetime.now(timezone.utc),
        updated_at=datetime.now(timezone.utc),
        **image_create.model_dump()
    ) for image_create in image_creates]

    await execute(
        insert(image).values([image_in_db.model_dump()
                              for image_in_db in images_in_db]),
        commit_after=True
    )
    return images_in_db


async def create_echarts(echart_creates: List[EchartCreate]) -> List[EchartInDB]:
    echarts_in_db = [EchartInDB(
        id=uuid.uuid4(),
        created_at=datetime.now(timezone.utc),
        updated_at=datetime.now(timezone.utc),
        **echart_create.model_dump()
    ) for echart_create in echart_creates]
    await execute(insert(echart).values([echart_in_db.model_dump() for echart_in_db in echarts_in_db]), commit_after=True)
    return echarts_in_db


async def create_tables(table_creates: List[TableCreate]) -> List[TableInDB]:
    tables_in_db = [TableInDB(
        id=uuid.uuid4(),
        created_at=datetime.now(timezone.utc),
        updated_at=datetime.now(timezone.utc),
        **table_create.model_dump()
    ) for table_create in table_creates]
    await execute(insert(table).values([table_in_db.model_dump() for table_in_db in tables_in_db]), commit_after=True)
    return tables_in_db


async def get_images(image_ids: List[uuid.UUID]) -> List[ImageInDB]:
    images = await fetch_all(select(image).where(image.c.id.in_(image_ids)))
    return [ImageInDB(**image) for image in images]


async def get_echarts(echart_ids: List[uuid.UUID]) -> List[EchartInDB]:
    echarts = await fetch_all(select(echart).where(echart.c.id.in_(echart_ids)))
    return [EchartInDB(**echart) for echart in echarts]


async def get_tables(table_ids: List[uuid.UUID]) -> List[TableInDB]:
    tables = await fetch_all(select(table).where(table.c.id.in_(table_ids)))
    return [TableInDB(**table) for table in tables]
