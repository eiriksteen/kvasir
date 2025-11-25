from uuid import UUID
from typing import List, Dict, Optional
from dataclasses import dataclass, field

from kvasir_agents.agents.v1.kvasir.knowledge_bank import SUPPORTED_TASKS_LITERAL
from kvasir_agents.agents.v1.base_agent import AgentDeps


@dataclass(kw_only=True)
class SWEDeps(AgentDeps):
    kvasir_run_id: UUID
    data_paths: List[str]
    read_only_paths: List[str]
    time_limit: int
    guidelines: List[SUPPORTED_TASKS_LITERAL] = field(default_factory=list)
    modified_files: Dict[str, str] = field(default_factory=dict)
    pipeline_id: Optional[UUID] = None

    def __post_init__(self):
        super().__post_init__()
        if isinstance(self.kvasir_run_id, str):
            self.kvasir_run_id = UUID(self.kvasir_run_id)
        if isinstance(self.pipeline_id, str):
            self.pipeline_id = UUID(self.pipeline_id)

    def to_dict(self) -> dict:
        return {
            **super().to_dict(),
            "kvasir_run_id": str(self.kvasir_run_id),
            "data_paths": self.data_paths,
            "read_only_paths": self.read_only_paths,
            "time_limit": self.time_limit,
            "guidelines": self.guidelines,
            "modified_files": self.modified_files,
            "pipeline_id": str(self.pipeline_id) if self.pipeline_id else None
        }
