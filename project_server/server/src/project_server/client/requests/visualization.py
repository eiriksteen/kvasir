from typing import List
from uuid import UUID

from project_server.client import ProjectClient
from synesis_schemas.main_server import (
    ImageCreate,
    ImageInDB,
    EchartCreate,
    EchartInDB,
    TableCreate,
    TableInDB,
)


async def get_image(client: ProjectClient, image_id: UUID) -> ImageInDB:
    response = await client.send_request(
        "get",
        f"/visualization/images/{image_id}",
    )
    return ImageInDB(**response.body)


async def create_images(client: ProjectClient, image_creates: List[ImageCreate]) -> List[ImageInDB]:
    response = await client.send_request(
        "post",
        "/visualization/images",
        json=[image.model_dump(mode="json") for image in image_creates]
    )
    return [ImageInDB(**image) for image in response.body]


async def get_echart(client: ProjectClient, echart_id: UUID) -> EchartInDB:
    response = await client.send_request(
        "get",
        f"/visualization/echarts/{echart_id}",
    )
    return EchartInDB(**response.body)


async def create_echarts(client: ProjectClient, echart_creates: List[EchartCreate]) -> List[EchartInDB]:
    response = await client.send_request(
        "post",
        "/visualization/echarts",
        json=[echart.model_dump(mode="json") for echart in echart_creates]
    )
    return [EchartInDB(**echart) for echart in response.body]


async def get_table(client: ProjectClient, table_id: UUID) -> TableInDB:
    response = await client.send_request(
        "get",
        f"/visualization/tables/{table_id}",
    )
    return TableInDB(**response.body)


async def create_tables(client: ProjectClient, table_creates: List[TableCreate]) -> List[TableInDB]:
    response = await client.send_request(
        "post",
        "/visualization/tables",
        json=[table.model_dump(mode="json") for table in table_creates]
    )
    return [TableInDB(**table) for table in response.body]
