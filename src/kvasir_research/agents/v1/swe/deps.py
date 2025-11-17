from uuid import UUID
from typing import List, Dict, Literal
from dataclasses import dataclass, field

from kvasir_research.agents.v1.kvasir.knowledge_bank import SUPPORTED_TASKS_LITERAL
from kvasir_research.agents.v1.callbacks import KvasirV1Callbacks
from kvasir_research.sandbox.abstract import AbstractSandbox
from kvasir_research.sandbox.local import LocalSandbox
from kvasir_research.sandbox.modal import ModalSandbox


@dataclass
class SWEDeps:
    run_id: UUID
    run_name: str
    project_id: UUID
    package_name: str
    data_paths: List[str]
    injected_analyses: List[UUID]
    injected_swe_runs: List[UUID]
    read_only_paths: List[str]
    time_limit: int
    guidelines: List[SUPPORTED_TASKS_LITERAL] = field(default_factory=list)
    modified_files: Dict[str, str] = field(default_factory=dict)
    sandbox: AbstractSandbox = field(init=False)
    sandbox_type: Literal["local", "modal"] = "local"
    callbacks: KvasirV1Callbacks = field(default_factory=KvasirV1Callbacks)

    def __post_init__(self):
        if self.sandbox_type == "local":
            self.sandbox = LocalSandbox(self.project_id, self.package_name)
        elif self.sandbox_type == "modal":
            self.sandbox = ModalSandbox(self.project_id, self.package_name)
        else:
            raise ValueError(f"Invalid sandbox type: {self.sandbox_type}")
