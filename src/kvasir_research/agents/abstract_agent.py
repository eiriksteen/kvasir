from abc import ABC, abstractmethod
from uuid import UUID
from typing import Literal, Optional
from pydantic import BaseModel

from kvasir_research.agents.abstract_callbacks import AbstractCallbacks
from kvasir_research.sandbox.local import LocalSandbox
from kvasir_research.sandbox.modal import ModalSandbox

"""
Class for standardized agent interface to facilitate agent reuse and iteration. 
Inputs:
- Run ID
- Project ID
- Package name
- Sandbox type (local or modal)
- Logger, including message for selected tool calls / output submissions with desired log 
- Callbacks for selected tool calls / output submissions (insert to DB, launch another agent based on result, etc)
"""


class AbstractAgentOutput(BaseModel):
    response: str


class AbstractAgent(ABC):
    def __init__(
        self,
        project_id: UUID,
        package_name: str,
        sandbox_type: Literal["local", "modal"],
        callbacks: AbstractCallbacks,
        run_id: Optional[UUID] = None
    ):
        self.run_id = run_id
        self.project_id = project_id
        self.package_name = package_name
        self.sandbox_type = sandbox_type
        self.callbacks = callbacks

        if self.sandbox_type == "local":
            self.sandbox = LocalSandbox(project_id, package_name)
        elif self.sandbox_type == "modal":
            self.sandbox = ModalSandbox(project_id, package_name)

    @abstractmethod
    async def __call__(self, prompt: str) -> AbstractAgentOutput:
        pass
