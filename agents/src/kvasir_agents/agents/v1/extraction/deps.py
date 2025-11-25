from uuid import UUID
from dataclasses import dataclass, field
from typing import List

from kvasir_ontology.entities.dataset.data_model import Dataset
from kvasir_agents.agents.v1.base_agent import AgentDeps


@dataclass(kw_only=True)
class ExtractionDeps(AgentDeps):
    created_datasets: List[Dataset] = field(default_factory=list)
    object_groups_with_charts: List[UUID] = field(default_factory=list)

    def __post_init__(self):
        super().__post_init__()

        self.object_groups_with_charts = [
            UUID(item) if isinstance(item, str) else item
            for item in self.object_groups_with_charts
        ]

        self.created_datasets = [
            Dataset.model_validate(item) if isinstance(item, dict) else item
            for item in self.created_datasets
        ]

    def to_dict(self) -> dict:
        return {
            **super().to_dict(),
            "object_groups_with_charts": [str(chart) for chart in self.object_groups_with_charts],
            "created_datasets": [dataset.model_dump(mode='json') for dataset in self.created_datasets]
        }
