from uuid import UUID
from typing import Literal, Optional
from dataclasses import dataclass, field

from kvasir_research.sandbox.abstract import AbstractSandbox
from kvasir_research.sandbox.local import LocalSandbox
from kvasir_research.sandbox.modal import ModalSandbox
from kvasir_research.agents.v1.callbacks import KvasirV1Callbacks
from kvasir_ontology.ontology import Ontology


@dataclass
class AgentDeps:
    project_id: UUID
    package_name: str
    user_id: Optional[UUID] = None
    run_id: Optional[UUID] = None
    run_name: Optional[str] = None
    bearer_token: Optional[str] = None
    sandbox_type: Literal["local", "modal"] = "local"


@dataclass(kw_only=True)
class AgentDepsFull(AgentDeps):
    ontology: Ontology
    callbacks: KvasirV1Callbacks = field(default_factory=KvasirV1Callbacks)
    sandbox: Optional[AbstractSandbox] = None

    def __post_init__(self):
        if self.sandbox is None:
            if self.sandbox_type == "local":
                self.sandbox = LocalSandbox(self.project_id, self.package_name)
            elif self.sandbox_type == "modal":
                self.sandbox = ModalSandbox(self.project_id, self.package_name)
            else:
                raise ValueError(f"Invalid sandbox type: {self.sandbox_type}")
