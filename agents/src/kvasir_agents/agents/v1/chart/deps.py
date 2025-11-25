from uuid import UUID
from dataclasses import dataclass, field
from typing import List, Optional

from kvasir_ontology.entities.dataset.data_model import ObjectGroup
from kvasir_agents.agents.v1.base_agent import AgentDeps


@dataclass(kw_only=True)
class ChartDeps(AgentDeps):
    base_code: Optional[str] = None
    object_group: Optional[ObjectGroup] = None

    def __post_init__(self):
        super().__post_init__()
        if isinstance(self.object_group, dict):
            self.object_group = ObjectGroup.model_validate(self.object_group)

    def to_dict(self) -> dict:
        return {
            **super().to_dict(),
            "base_code": self.base_code,
            "object_group": self.object_group.model_dump(mode='json') if self.object_group else None
        }
