from abc import ABC, abstractmethod
from uuid import UUID
from typing import Literal


class AbstractCallbacks(ABC):
    """
    Class to run code during agent run for connecting to an application (streaming, saving to DB, etc)
    """

    @abstractmethod
    async def log(self, run_id: UUID, message: str, type: Literal["result", "tool_call", "error"]) -> None:
        pass
