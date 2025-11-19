from uuid import UUID
from typing import List, Dict
from dataclasses import dataclass, field

from kvasir_research.agents.v1.kvasir.knowledge_bank import SUPPORTED_TASKS_LITERAL
from kvasir_research.agents.v1.deps import AgentDepsFull


@dataclass(kw_only=True)
class SWEDeps(AgentDepsFull):
    kvasir_run_id: UUID
    data_paths: List[str]
    injected_analyses: List[UUID]
    injected_swe_runs: List[UUID]
    read_only_paths: List[str]
    time_limit: int
    guidelines: List[SUPPORTED_TASKS_LITERAL] = field(default_factory=list)
    modified_files: Dict[str, str] = field(default_factory=dict)
