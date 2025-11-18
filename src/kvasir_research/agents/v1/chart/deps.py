from uuid import UUID
from dataclasses import dataclass, field
from typing import List, Optional

from kvasir_ontology.entities.dataset.data_model import ObjectGroup
from kvasir_research.agents.v1.deps import AgentDepsFull


@dataclass(kw_only=True)
class ChartDeps(AgentDepsFull):
    datasets_injected: List[UUID] = field(default_factory=list)
    data_sources_injected: List[UUID] = field(default_factory=list)
    base_code: Optional[str] = None
    object_group: Optional[ObjectGroup] = None
