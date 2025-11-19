from uuid import UUID
from dataclasses import dataclass, field
from typing import List, Optional

from kvasir_ontology.entities.dataset.data_model import ObjectGroup
from kvasir_research.agents.v1.base_agent import AgentDeps


@dataclass(kw_only=True)
class ChartDeps(AgentDeps):
    datasets_injected: List[UUID] = field(default_factory=list)
    data_sources_injected: List[UUID] = field(default_factory=list)
    base_code: Optional[str] = None
    object_group: Optional[ObjectGroup] = None

    def __post_init__(self):
        super().__post_init__()
        if isinstance(self.datasets_injected, list):
            self.datasets_injected = AgentDeps._convert_uuid_list(self.datasets_injected)
        if isinstance(self.data_sources_injected, list):
            self.data_sources_injected = AgentDeps._convert_uuid_list(self.data_sources_injected)

    def _get_non_serializable_fields(self) -> set:
        result = super()._get_non_serializable_fields()
        result.add("object_group")
        return result
