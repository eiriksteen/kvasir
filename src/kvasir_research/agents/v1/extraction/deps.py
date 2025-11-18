from uuid import UUID
from dataclasses import dataclass, field
from typing import List

from kvasir_ontology.entities.dataset.data_model import Dataset
from kvasir_research.agents.v1.deps import AgentDepsFull


@dataclass(kw_only=True)
class ExtractionDeps(AgentDepsFull):
    created_datasets: List[Dataset] = field(default_factory=list)
    object_groups_with_charts: List[UUID] = field(default_factory=list)
