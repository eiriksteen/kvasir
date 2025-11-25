from uuid import UUID
from abc import ABC, abstractmethod
from typing import List, Optional, Tuple
from pathlib import Path
from io import BytesIO

from kvasir_ontology.entities.data_source.data_model import DataSource, DataSourceCreate, DataSourceDetailsCreate


class DataSourceInterface(ABC):

    def __init__(self, user_id: UUID, bearer_token: Optional[str] = None):
        self.user_id = user_id
        self.bearer_token = bearer_token

    @abstractmethod
    async def create_data_source(self, data_source: DataSourceCreate) -> DataSource:
        pass

    @abstractmethod
    async def add_data_source_details(self, data_source_id: UUID, data_source_details: DataSourceDetailsCreate) -> DataSource:
        pass

    @abstractmethod
    async def get_data_sources(self, data_source_ids: Optional[List[UUID]] = None) -> List[DataSource]:
        pass

    @abstractmethod
    async def get_data_source(self, data_source_id: UUID) -> DataSource:
        pass

    @abstractmethod
    async def delete_data_source(self, data_source_id: UUID) -> None:
        pass

    @abstractmethod
    async def create_files_data_sources(self, file_bytes: List[BytesIO], file_names: List[str], mount_group_id: UUID) -> Tuple[List[DataSource], List[Path]]:
        pass

    # Methods to get submission code for use in sandbox

    @abstractmethod
    async def get_data_source_details_submission_code(self) -> Tuple[str, str]:
        """
        Returns tuple of (submission code, submission description). 
        Final code should print a dictionary corresponding to the DataSourceDetails schema.
        Submission description must explain the code the agent should generate to enable the submission (variable names, etc.).
        """
        pass
