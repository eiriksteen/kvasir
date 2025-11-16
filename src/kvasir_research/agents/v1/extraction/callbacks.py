from uuid import UUID
from typing import List, Literal, Dict
from abc import abstractmethod
from pydantic_ai.models import ModelMessage
from taskiq import TaskiqState, TaskiqEvents

from kvasir_research.agents.abstract_callbacks import AbstractCallbacks
from kvasir_research.agents.v1.broker import v1_broker


class ExtractionV1Callbacks(AbstractCallbacks):

    def __init_subclass__(cls) -> None:
        super().__init_subclass__()

        def startup(state: TaskiqState) -> None:
            state.callbacks = cls()

        v1_broker.add_event_handler(
            TaskiqEvents.WORKER_STARTUP, startup)

    @abstractmethod
    async def save_extraction_deps(self, run_id: UUID, deps: Dict) -> None:
        pass

    @abstractmethod
    async def load_extraction_deps(self, run_id: UUID) -> Dict:
        pass

    @abstractmethod
    async def save_message_history(self, run_id: UUID, message_history: List[ModelMessage]) -> None:
        pass

    @abstractmethod
    async def get_message_history(self, run_id: UUID) -> List[ModelMessage]:
        pass
