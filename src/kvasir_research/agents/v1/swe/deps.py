from uuid import UUID
from typing import List, Dict
from dataclasses import dataclass, field

from kvasir_research.agents.v1.kvasir.knowledge_bank import SUPPORTED_TASKS_LITERAL
from kvasir_research.agents.v1.base_agent import AgentDeps


@dataclass(kw_only=True)
class SWEDeps(AgentDeps):
    kvasir_run_id: UUID
    data_paths: List[str]
    injected_analyses: List[UUID]
    injected_swe_runs: List[UUID]
    read_only_paths: List[str]
    time_limit: int
    guidelines: List[SUPPORTED_TASKS_LITERAL] = field(default_factory=list)
    modified_files: Dict[str, str] = field(default_factory=dict)

    def __post_init__(self):
        super().__post_init__()
        if isinstance(self.kvasir_run_id, str):
            self.kvasir_run_id = UUID(self.kvasir_run_id)

        if isinstance(self.injected_analyses, list):
            self.injected_analyses = AgentDeps._convert_uuid_list(
                self.injected_analyses)

        if isinstance(self.injected_swe_runs, list):
            self.injected_swe_runs = AgentDeps._convert_uuid_list(
                self.injected_swe_runs)
