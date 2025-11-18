from uuid import UUID
from typing import List
from dataclasses import dataclass, field

from kvasir_research.agents.v1.deps import AgentDepsFull


@dataclass(kw_only=True)
class KvasirV1Deps(AgentDepsFull):
    launched_analysis_run_ids: List[UUID] = field(default_factory=list)
    launched_swe_run_ids: List[UUID] = field(default_factory=list)
