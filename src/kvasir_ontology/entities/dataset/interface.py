import pandas as pd
from abc import ABC, abstractmethod
from uuid import UUID
from typing import List, Optional, Tuple, Union, Dict

from kvasir_ontology.entities.dataset.data_model import Dataset, DatasetCreate, ObjectGroup, ObjectGroupWithObjects, ObjectGroupCreate, ObjectsFile, DataObject
from kvasir_ontology.visualization.data_model import EchartCreate


class DatasetInterface(ABC):

    def __init__(self, user_id: UUID, bearer_token: Optional[str] = None):
        self.user_id = user_id
        self.bearer_token = bearer_token

    @abstractmethod
    async def create_dataset(self, dataset: DatasetCreate, filename_to_dataframe: Optional[Dict[str, pd.DataFrame]] = None) -> Dataset:
        pass

    @abstractmethod
    async def add_object_group(self, dataset_id: UUID, object_group: ObjectGroupCreate, filename_to_dataframe: Dict[str, pd.DataFrame]) -> ObjectGroup:
        pass

    @abstractmethod
    async def add_data_objects(self, object_group_id: UUID, metadata: List[ObjectsFile], filename_to_dataframe: Dict[str, pd.DataFrame]) -> List[DataObject]:
        pass

    @abstractmethod
    async def get_dataset(self, dataset_id: UUID) -> Dataset:
        pass

    @abstractmethod
    async def get_datasets(self, dataset_ids: Optional[List[UUID]] = None) -> List[Dataset]:
        pass

    @abstractmethod
    async def get_object_group(self, group_id: UUID) -> ObjectGroup:
        pass

    @abstractmethod
    async def get_object_groups(
        self,
        group_ids: Optional[List[UUID]] = None,
        dataset_id: Optional[UUID] = None,
        include_objects: bool = False,
    ) -> List[Union[ObjectGroup, ObjectGroupWithObjects]]:
        pass

    @abstractmethod
    async def get_data_object(self, object_id: UUID) -> DataObject:
        pass

    @abstractmethod
    async def get_data_objects(
        self,
        object_ids: Optional[List[UUID]] = None,
        group_ids: Optional[List[UUID]] = None
    ) -> List[DataObject]:
        pass

    @abstractmethod
    async def create_object_group_echart(self, object_group_id: UUID, echart: EchartCreate) -> ObjectGroup:
        pass

    @abstractmethod
    async def delete_dataset(self, dataset_id: UUID) -> None:
        pass

    @abstractmethod
    async def get_object_group_submission_code(self) -> Tuple[str, str]:
        """
        Returns tuple of (submission code, submission description). 
        """
        pass
