from uuid import UUID
from typing import List, Literal, Dict
from abc import abstractmethod
from pydantic_ai.models import ModelMessage
from taskiq import TaskiqState, TaskiqEvents

from kvasir_research.agents.abstract_callbacks import AbstractCallbacks
from kvasir_research.agents.v1.broker import v1_broker


class KvasirV1Callbacks(AbstractCallbacks):

    def __init_subclass__(cls) -> None:
        super().__init_subclass__()

        def startup(state: TaskiqState) -> None:
            state.callbacks = cls()

        v1_broker.add_event_handler(
            TaskiqEvents.WORKER_STARTUP, startup)

    @abstractmethod
    async def check_orchestrator_run_exists(self, run_id: UUID) -> bool:
        pass

    @abstractmethod
    async def get_orchestrator_run_status(self, run_id: UUID) -> Literal["pending", "completed", "failed", "waiting", "running"]:
        pass

    @abstractmethod
    async def set_orchestrator_run_status(self, run_id: UUID, status: Literal["pending", "completed", "failed", "waiting", "running"]) -> str:
        pass

    @abstractmethod
    async def get_results_queue(self, run_id: UUID) -> List[str]:
        pass

    @abstractmethod
    async def pop_result_from_queue(self, run_id: UUID) -> str:
        pass

    @abstractmethod
    async def add_result_to_queue(self, run_id: UUID, result: str) -> None:
        pass

    @abstractmethod
    async def save_orchestrator_deps(self, run_id: UUID, deps: Dict) -> None:
        pass

    @abstractmethod
    async def load_orchestrator_deps(self, run_id: UUID) -> Dict:
        pass

    @abstractmethod
    async def save_swe_deps(self, run_id: UUID, deps: Dict) -> None:
        pass

    @abstractmethod
    async def load_swe_deps(self, run_id: UUID) -> Dict:
        pass

    @abstractmethod
    async def save_swe_result(self, run_id: UUID, result: str) -> None:
        pass

    @abstractmethod
    async def get_swe_result(self, run_id: UUID) -> str:
        pass

    @abstractmethod
    async def save_analysis_deps(self, run_id: UUID, deps: Dict) -> None:
        pass

    @abstractmethod
    async def load_analysis_deps(self, run_id: UUID) -> Dict:
        pass

    @abstractmethod
    async def save_analysis_result(self, run_id: UUID, result: str) -> None:
        pass

    @abstractmethod
    async def get_analysis_result(self, run_id: UUID) -> str:
        pass

    @abstractmethod
    async def save_message_history(self, run_id: UUID, message_history: List[ModelMessage]) -> None:
        pass

    @abstractmethod
    async def get_message_history(self, run_id: UUID) -> List[ModelMessage]:
        pass
