from uuid import UUID, uuid4
from typing import List, Dict, Literal, Optional
from abc import abstractmethod, ABC

from kvasir_ontology.ontology import Ontology
from pydantic_ai.models import ModelMessage
from kvasir_agents.agents.v1.data_model import (
    AnalysisRun,
    SweRun,
    RunBase,
    RunCreate,
    MessageCreate,
    Message,
    RUN_TYPE_LITERAL,
)


class KvasirV1Callbacks(ABC):

    @abstractmethod
    async def log(self, user_id: UUID, run_id: UUID, message: str, type: Literal["result", "tool_call", "error", "info"]) -> None:
        pass

    @abstractmethod
    async def get_run_status(self, user_id: UUID, run_id: UUID) -> Literal["pending", "completed", "failed", "waiting", "running"]:
        pass

    @abstractmethod
    async def set_run_status(self, user_id: UUID, run_id: UUID, status: Literal["pending", "completed", "failed", "waiting", "running"]) -> str:
        pass

    @abstractmethod
    async def create_swe_run(
            self, user_id: UUID, project_id: UUID, kvasir_run_id: UUID, pipeline_id: UUID, run_name: str | None = None, initial_status: Literal["pending", "completed", "failed", "waiting", "running"] | None = None) -> SweRun:
        pass

    @abstractmethod
    async def create_analysis_run(
            self, user_id: UUID, project_id: UUID, kvasir_run_id: UUID, analysis_id: UUID, run_name: str | None = None, initial_status: Literal["pending", "completed", "failed", "waiting", "running"] | None = None) -> AnalysisRun:
        pass

    @abstractmethod
    async def create_kvasir_run(self, user_id: UUID, project_id: UUID, run_name: str | None = None, initial_status: Literal["pending", "completed", "failed", "waiting", "running"] | None = None) -> RunBase:
        pass

    @abstractmethod
    async def get_analysis_run(self, user_id: UUID, run_id: UUID) -> AnalysisRun:
        pass

    @abstractmethod
    async def get_swe_run(self, user_id: UUID, run_id: UUID) -> SweRun:
        pass

    @abstractmethod
    async def create_extraction_run(self, user_id: UUID, project_id: UUID, run_name: str | None = None, initial_status: Literal["pending", "completed", "failed", "waiting", "running"] | None = None) -> RunBase:
        pass

    @abstractmethod
    async def save_message_history(self, user_id: UUID, run_id: UUID, message_history: List[ModelMessage]) -> None:
        pass

    @abstractmethod
    async def get_message_history(self, user_id: UUID, run_id: UUID) -> List[ModelMessage] | None:
        pass

    @abstractmethod
    async def save_deps(self, user_id: UUID, run_id: UUID, deps: Dict) -> None:
        pass

    @abstractmethod
    async def load_deps(self, user_id: UUID, run_id: UUID) -> Dict:
        pass

    @abstractmethod
    def create_ontology(self, user_id: UUID, mount_node_id: UUID, bearer_token: Optional[str] = None) -> Ontology:
        pass

    @abstractmethod
    async def get_runs(
        self,
        user_id: UUID,
        run_ids: Optional[List[UUID]] = None,
        project_id: Optional[UUID] = None,
        status: Optional[str] = None,
        filter_status: Optional[List[str]] = None,
        type: Optional[RUN_TYPE_LITERAL] = None
    ) -> List[RunBase]:
        pass

    @abstractmethod
    async def get_messages(
        self,
        user_id: UUID,
        run_id: UUID,
        type: Optional[Literal["tool_call", "result", "error"]] = None
    ) -> List[Message]:
        pass

    @abstractmethod
    async def create_message(self, user_id: UUID, create: MessageCreate) -> Message:
        pass

    @abstractmethod
    async def update_run_name(self, user_id: UUID, run_id: UUID, name: str) -> RunBase:
        pass

    @abstractmethod
    async def create_run(self, user_id: UUID, create: RunCreate) -> RunBase:
        pass

    @abstractmethod
    async def get_runs_status_description(self, user_id: UUID, kvasir_run_id: UUID) -> str:
        pass
