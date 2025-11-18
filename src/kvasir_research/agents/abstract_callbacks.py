from abc import ABC, abstractmethod
from uuid import UUID
from typing import Literal, List, Optional
from pydantic_ai.models import ModelMessage

from kvasir_ontology.ontology import Ontology


class AbstractCallbacks(ABC):
    """
    Class to run code during agent run for connecting to an application (streaming, saving to DB, etc)
    """

    @abstractmethod
    async def log(self, run_id: UUID, message: str, type: Literal["result", "tool_call", "error"]) -> None:
        pass

    @abstractmethod
    async def get_run_status(self, run_id: UUID) -> Literal["pending", "completed", "failed", "waiting", "running"]:
        pass

    @abstractmethod
    async def set_run_status(self, run_id: UUID, status: Literal["pending", "completed", "failed", "waiting", "running"]) -> str:
        pass

    @abstractmethod
    async def create_run(self, user_id: UUID, project_id: UUID, run_type: Literal["swe", "analysis", "chart", "extraction", "kvasir"]) -> UUID:
        pass

    @abstractmethod
    async def complete_run(self, run_id: UUID, output: str) -> None:
        pass

    @abstractmethod
    async def fail_run(self, run_id: UUID, error: str) -> None:
        pass

    @abstractmethod
    async def save_message_history(self, run_id: UUID, message_history: List[ModelMessage]) -> None:
        pass

    @abstractmethod
    async def get_message_history(self, run_id: UUID) -> List[ModelMessage] | None:
        pass

    @abstractmethod
    def create_ontology(self, user_id: UUID, mount_group_id: UUID, bearer_token: Optional[str] = None) -> Ontology:
        pass
