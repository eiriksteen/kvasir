from uuid import UUID
from dataclasses import dataclass, field
from typing import List

from kvasir_ontology.entities.dataset.data_model import Dataset
from kvasir_research.agents.v1.base_agent import AgentDeps


@dataclass(kw_only=True)
class ExtractionDeps(AgentDeps):
    created_datasets: List[Dataset] = field(default_factory=list)
    object_groups_with_charts: List[UUID] = field(default_factory=list)

    def __post_init__(self):
        super().__post_init__()
        if isinstance(self.object_groups_with_charts, list):
            self.object_groups_with_charts = AgentDeps._convert_uuid_list(
                self.object_groups_with_charts)

    def _get_non_serializable_fields(self) -> set:
        result = super()._get_non_serializable_fields()
        result.add("created_datasets")
        return result
