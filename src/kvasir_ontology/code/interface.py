from abc import ABC, abstractmethod
from uuid import UUID
from typing import List

from kvasir_ontology.code.data_model import CodebaseFile, CodebasePath


class CodeInterface(ABC):

    def __init__(self, user_id: UUID, mount_group_id: UUID):
        self.user_id = user_id
        self.mount_group_id = mount_group_id

    @abstractmethod
    async def get_codebase_tree(self) -> CodebasePath:
        pass

    @abstractmethod
    async def get_codebase_file(self, file_path: str) -> CodebaseFile:
        pass
