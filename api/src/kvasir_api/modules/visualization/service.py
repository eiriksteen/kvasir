import json
import uuid
import modal
from datetime import datetime, timezone
from typing import List, Annotated, Optional
from sqlalchemy import insert, select, and_
from fastapi import Depends, HTTPException

from kvasir_api.database.service import execute, fetch_all
from kvasir_api.modules.visualization.models import image, echart, table
from kvasir_api.modules.entity_graph.service import EntityGraphs
from kvasir_api.auth.service import get_current_user
from kvasir_api.auth.schema import User

from kvasir_ontology.visualization.interface import VisualizationInterface
from kvasir_ontology.visualization.data_model import ImageBase, EchartBase, TableBase, ImageCreate, EchartCreate, TableCreate, EChartsOption

from kvasir_agents.sandbox.modal import ModalSandbox


class Visualizations(VisualizationInterface):

    def __init__(self, user_id: uuid.UUID):
        super().__init__(user_id)

    async def create_image(self, image_create: ImageCreate) -> ImageBase:
        images = await self.create_images([image_create])
        return images[0]

    async def create_echart(self, echart_create: EchartCreate) -> EchartBase:
        echarts = await self.create_echarts([echart_create])
        return echarts[0]

    async def create_table(self, table_create: TableCreate) -> TableBase:
        tables = await self.create_tables([table_create])
        return tables[0]

    async def get_image(self, image_id: uuid.UUID) -> ImageBase:
        images = await self.get_images([image_id])
        return images[0]

    async def get_echart(self, echart_id: uuid.UUID) -> EchartBase:
        echarts = await self.get_echarts([echart_id])
        return echarts[0]

    async def get_table(self, table_id: uuid.UUID) -> TableBase:
        tables = await self.get_tables([table_id])
        return tables[0]

    async def create_images(self, image_creates: List[ImageCreate]) -> List[ImageBase]:
        now = datetime.now(timezone.utc)
        image_values = [
            ImageBase(
                id=uuid.uuid4(),
                user_id=self.user_id,
                image_path=img_create.image_path,
                created_at=now,
                updated_at=now,
            )
            for img_create in image_creates
        ]

        await execute(
            insert(image).values([img.model_dump() for img in image_values]),
            commit_after=True
        )
        return image_values

    async def create_echarts(self, echart_creates: List[EchartCreate]) -> List[EchartBase]:
        now = datetime.now(timezone.utc)
        echart_values = [
            EchartBase(
                id=uuid.uuid4(),
                user_id=self.user_id,
                chart_script_path=echart_create.chart_script_path,
                created_at=now,
                updated_at=now,
            )
            for echart_create in echart_creates
        ]
        await execute(insert(echart).values([ech.model_dump() for ech in echart_values]), commit_after=True)
        return echart_values

    async def create_tables(self, table_creates: List[TableCreate]) -> List[TableBase]:
        now = datetime.now(timezone.utc)
        table_values = [
            TableBase(
                id=uuid.uuid4(),
                user_id=self.user_id,
                table_path=table_create.table_path,
                created_at=now,
                updated_at=now,
            )
            for table_create in table_creates
        ]
        await execute(insert(table).values([tbl.model_dump() for tbl in table_values]), commit_after=True)
        return table_values

    async def get_images(self, image_ids: List[uuid.UUID]) -> List[ImageBase]:
        image_records = await fetch_all(
            select(image).where(
                and_(
                    image.c.id.in_(image_ids),
                    image.c.user_id == self.user_id
                )
            )
        )
        return [ImageBase(**img) for img in image_records]

    async def get_echarts(self, echart_ids: List[uuid.UUID]) -> List[EchartBase]:
        echart_records = await fetch_all(
            select(echart).where(
                and_(
                    echart.c.id.in_(echart_ids),
                    echart.c.user_id == self.user_id
                )
            )
        )
        return [EchartBase(**ech) for ech in echart_records]

    async def get_tables(self, table_ids: List[uuid.UUID]) -> List[TableBase]:
        table_records = await fetch_all(
            select(table).where(
                and_(
                    table.c.id.in_(table_ids),
                    table.c.user_id == self.user_id
                )
            )
        )
        return [TableBase(**tbl) for tbl in table_records]

    async def download_image(self, image_id: uuid.UUID, mount_node_id: uuid.UUID) -> bytes:
        image_obj = await self.get_image(image_id)
        vol = modal.Volume.from_name(
            str(mount_node_id), create_if_missing=True)

        chunks = []
        async for chunk in vol.read_file.aio(image_obj.image_path.replace("/app", "")):
            chunks.append(chunk)

        return b"".join(chunks)

    async def download_table(self, table_id: uuid.UUID, mount_node_id: uuid.UUID) -> bytes:
        table_obj = await self.get_table(table_id)

        vol = modal.Volume.from_name(
            str(mount_node_id), create_if_missing=True)

        chunks = []
        async for chunk in vol.read_file.aio(table_obj.table_path.replace("/app", "")):
            chunks.append(chunk)

        return b"".join(chunks)

    async def download_echart(self, echart_id: uuid.UUID, mount_node_id: uuid.UUID, original_object_id: Optional[str] = None) -> EChartsOption:
        graph_service = EntityGraphs(self.user_id)
        mount_node = await graph_service.get_node(mount_node_id)
        if not mount_node.python_package_name:
            raise HTTPException(
                status_code=400,
                detail=f"Mount node with ID {mount_node_id} does not have a Python package name"
            )

        echart = await self.get_echart(echart_id)
        sandbox = ModalSandbox(mount_node_id,
                               mount_node.python_package_name)
        script_content = await sandbox.read_file(echart.chart_script_path)

        if original_object_id:
            script_content = f"{script_content}\n\nresult = generate_chart('{original_object_id}')\nimport json\nprint(json.dumps(result, default=str))"
        else:
            script_content = f"{script_content}\n\nresult = generate_chart()\nimport json\nprint(json.dumps(result, default=str))"

        out, err = await sandbox.run_python_code(script_content)

        if err:
            raise HTTPException(
                status_code=500,
                detail=f"Chart script execution error: {err}"
            )

        result_data = json.loads(out.strip())
        chart_config = EChartsOption(**result_data)

        return chart_config


# For dependency injection
async def get_visualization_service(user: Annotated[User, Depends(get_current_user)]) -> VisualizationInterface:
    return Visualizations(user.id)
