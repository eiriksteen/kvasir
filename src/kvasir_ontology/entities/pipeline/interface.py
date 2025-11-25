from abc import ABC, abstractmethod
from uuid import UUID
from typing import List, Optional


from kvasir_ontology.entities.pipeline.data_model import (
    Pipeline,
    PipelineCreate,
    PipelineImplementationCreate,
    PipelineRunBase,
    PipelineRunCreate,
    PIPELINE_RUN_STATUS_LITERAL
)


class PipelineInterface(ABC):

    def __init__(self, user_id: UUID):
        self.user_id = user_id

    @abstractmethod
    async def create_pipeline(self, pipeline: PipelineCreate) -> Pipeline:
        pass

    @abstractmethod
    async def create_pipeline_implementation(self, pipeline_implementation: PipelineImplementationCreate) -> Pipeline:
        pass

    @abstractmethod
    async def create_pipeline_run(self, pipeline_run: PipelineRunCreate) -> PipelineRunBase:
        pass

    @abstractmethod
    async def create_pipeline_runs(self, pipeline_runs: List[PipelineRunCreate]) -> List[PipelineRunBase]:
        pass

    @abstractmethod
    async def get_pipeline(self, pipeline_id: UUID) -> Pipeline:
        pass

    @abstractmethod
    async def get_pipelines(self, pipeline_ids: Optional[List[UUID]] = None) -> List[Pipeline]:
        pass

    @abstractmethod
    async def get_pipeline_runs(
        self,
        only_running: bool = False,
        pipeline_ids: Optional[List[UUID]] = None,
        run_ids: Optional[List[UUID]] = None
    ) -> List[PipelineRunBase]:
        pass

    @abstractmethod
    async def get_pipeline_run(self, pipeline_run_id: UUID) -> PipelineRunBase:
        pass

    @abstractmethod
    async def update_pipeline_run_status(self, pipeline_run_id: UUID, status: PIPELINE_RUN_STATUS_LITERAL) -> PipelineRunBase:
        pass

    @abstractmethod
    async def delete_pipeline(self, pipeline_id: UUID) -> None:
        pass
