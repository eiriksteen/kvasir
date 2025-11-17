import uuid
from dataclasses import dataclass, field
from typing import List, Optional, Literal


from kvasir_research.sandbox.abstract import AbstractSandbox
from kvasir_research.sandbox.local import LocalSandbox
from kvasir_research.sandbox.modal import ModalSandbox
from kvasir_research.agents.v1.callbacks import KvasirV1Callbacks
from kvasir_ontology.entities.dataset.data_model import ObjectGroup


@dataclass
class ChartDeps:
    project_id: uuid.UUID
    package_name: str
    sandbox: AbstractSandbox
    sandbox_type: Literal["local", "modal"] = "local"
    datasets_injected: List[uuid.UUID] = field(default_factory=list)
    data_sources_injected: List[uuid.UUID] = field(default_factory=list)
    # Pre-executed code with computed variables
    base_code: Optional[str] = None
    # If set, chart is for object group (takes object_id param)
    object_group: Optional[ObjectGroup] = None
    callbacks: KvasirV1Callbacks

    def __post_init__(self):
        if self.sandbox_type == "local":
            self.sandbox = LocalSandbox(self.project_id, self.package_name)
        elif self.sandbox_type == "modal":
            self.sandbox = ModalSandbox(self.project_id, self.package_name)
        else:
            raise ValueError(f"Invalid sandbox type: {self.sandbox_type}")
