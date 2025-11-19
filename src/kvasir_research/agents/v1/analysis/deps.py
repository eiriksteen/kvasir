from uuid import UUID
from typing import List, OrderedDict, Tuple, Literal, Optional
from collections import OrderedDict as OrderedDictType
from dataclasses import dataclass, field

from kvasir_research.agents.v1.kvasir.knowledge_bank import SUPPORTED_TASKS_LITERAL
from kvasir_research.agents.v1.base_agent import AgentDeps


@dataclass(kw_only=True)
class AnalysisDeps(AgentDeps):
    kvasir_run_id: UUID
    data_paths: List[str]
    injected_analyses: List[UUID]
    time_limit: int
    # Key: name, value: (type, content), content is code, markdown, or output
    notebook: OrderedDict[str,
                          Tuple[Literal["code", "markdown", "output"], str]]
    guidelines: List[SUPPORTED_TASKS_LITERAL] = field(default_factory=list)
    analysis_id: Optional[UUID] = None

    def __post_init__(self):
        super().__post_init__()
        if isinstance(self.kvasir_run_id, str):
            self.kvasir_run_id = UUID(self.kvasir_run_id)

        if isinstance(self.injected_analyses, list):
            self.injected_analyses = AgentDeps._convert_uuid_list(
                self.injected_analyses)

        if self.analysis_id is not None and isinstance(self.analysis_id, str):
            self.analysis_id = UUID(self.analysis_id)

        if isinstance(self.notebook, dict) and type(self.notebook) is not OrderedDictType:
            notebook = OrderedDictType()
            for k, v in self.notebook.items():
                if isinstance(v, list):
                    notebook[k] = tuple(v)
                else:
                    notebook[k] = v
            self.notebook = notebook
