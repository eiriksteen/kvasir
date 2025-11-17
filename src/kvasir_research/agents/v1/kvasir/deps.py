from dataclasses import dataclass, field
from typing import List, Literal
from uuid import UUID


from kvasir_research.sandbox.abstract import AbstractSandbox
from kvasir_research.sandbox.local import LocalSandbox
from kvasir_research.sandbox.modal import ModalSandbox


@dataclass
class KvasirV1Deps:
    run_id: UUID
    project_id: UUID
    package_name: str
    launched_analysis_run_ids: List[UUID] = field(default_factory=list)
    launched_swe_run_ids: List[UUID] = field(default_factory=list)
    sandbox: AbstractSandbox = field(init=False)
    sandbox_type: Literal["local", "modal"] = "local"

    def __post_init__(self):
        if self.sandbox_type == "local":
            self.sandbox = LocalSandbox(self.project_id, self.package_name)
        elif self.sandbox_type == "modal":
            self.sandbox = ModalSandbox(self.project_id, self.package_name)
        else:
            raise ValueError(f"Invalid sandbox type: {self.sandbox_type}")
