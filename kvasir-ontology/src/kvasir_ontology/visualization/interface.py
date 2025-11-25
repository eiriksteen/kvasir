from uuid import UUID
from typing import List, Optional
from abc import ABC, abstractmethod

from kvasir_ontology.visualization.data_model import ImageBase, EchartBase, TableBase, ImageCreate, EchartCreate, TableCreate, EChartsOption


class VisualizationInterface(ABC):

    def __init__(self, user_id: UUID):
        self.user_id = user_id

    @abstractmethod
    async def create_image(self, image: ImageCreate) -> ImageBase:
        pass

    @abstractmethod
    async def create_echart(self, echart: EchartCreate) -> EchartBase:
        pass

    @abstractmethod
    async def create_table(self, table: TableCreate) -> TableBase:
        pass

    @abstractmethod
    async def get_image(self, image_id: UUID) -> ImageBase:
        pass

    @abstractmethod
    async def get_echart(self, echart_id: UUID) -> EchartBase:
        pass

    @abstractmethod
    async def get_table(self, table_id: UUID) -> TableBase:
        pass

    @abstractmethod
    async def create_images(self, images: List[ImageCreate]) -> List[ImageBase]:
        pass

    @abstractmethod
    async def create_echarts(self, echarts: List[EchartCreate]) -> List[EchartBase]:
        pass

    @abstractmethod
    async def create_tables(self, tables: List[TableCreate]) -> List[TableBase]:
        pass

    @abstractmethod
    async def get_images(self, image_ids: List[UUID]) -> List[ImageBase]:
        pass

    @abstractmethod
    async def get_echarts(self, echart_ids: List[UUID]) -> List[EchartBase]:
        pass

    @abstractmethod
    async def get_tables(self, table_ids: List[UUID]) -> List[TableBase]:
        pass

    @abstractmethod
    async def download_image(self, image_id: UUID, mount_group_id: UUID) -> bytes:
        pass

    @abstractmethod
    async def download_table(self, table_id: UUID, mount_group_id: UUID) -> bytes:
        pass

    @abstractmethod
    async def download_echart(self, echart_id: UUID, mount_group_id: UUID, original_object_id: Optional[str] = None) -> EChartsOption:
        pass
