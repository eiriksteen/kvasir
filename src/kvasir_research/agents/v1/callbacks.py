from uuid import UUID
from typing import List, Dict
from abc import abstractmethod
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
