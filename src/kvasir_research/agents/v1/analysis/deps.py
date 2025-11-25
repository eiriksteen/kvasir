from uuid import UUID
from typing import List, Optional
from dataclasses import dataclass, field

from kvasir_research.agents.v1.kvasir.knowledge_bank import SUPPORTED_TASKS_LITERAL
from kvasir_research.agents.v1.base_agent import AgentDeps
from kvasir_ontology.entities.analysis.data_model import Analysis


@dataclass(kw_only=True)
class AnalysisDeps(AgentDeps):
    kvasir_run_id: UUID
    data_paths: List[str]
    time_limit: int
    guidelines: List[SUPPORTED_TASKS_LITERAL] = field(default_factory=list)
    analysis_id: Optional[UUID] = None
    # Will be set by agent during setup
    analysis: Optional[Analysis] = None

    def __post_init__(self):
        super().__post_init__()
        if isinstance(self.kvasir_run_id, str):
            self.kvasir_run_id = UUID(self.kvasir_run_id)
        if isinstance(self.analysis, dict):
            self.analysis = Analysis.model_validate(self.analysis)
        if isinstance(self.analysis_id, str):
            self.analysis_id = UUID(self.analysis_id)

    def to_dict(self) -> dict:
        return {
            **super().to_dict(),
            "kvasir_run_id": str(self.kvasir_run_id),
            "data_paths": self.data_paths,
            "time_limit": self.time_limit,
            "guidelines": self.guidelines,
            "analysis_id": str(self.analysis_id) if self.analysis_id else None
        }
