from uuid import UUID
from typing import List
from dataclasses import dataclass, field

from kvasir_research.agents.v1.base_agent import AgentDeps


@dataclass(kw_only=True)
class KvasirV1Deps(AgentDeps):
    launched_analysis_run_ids: List[UUID] = field(default_factory=list)
    launched_swe_run_ids: List[UUID] = field(default_factory=list)

    def __post_init__(self):
        super().__post_init__()
        if isinstance(self.launched_analysis_run_ids, list):
            self.launched_analysis_run_ids = [
                UUID(item) if isinstance(item, str) else item
                for item in self.launched_analysis_run_ids
            ]

        if isinstance(self.launched_swe_run_ids, list):
            self.launched_swe_run_ids = [
                UUID(item) if isinstance(item, str) else item
                for item in self.launched_swe_run_ids
            ]
