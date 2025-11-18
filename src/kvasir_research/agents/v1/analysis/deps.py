from uuid import UUID
from typing import List, OrderedDict, Tuple, Literal
from dataclasses import dataclass, field

from kvasir_research.agents.v1.kvasir.knowledge_bank import SUPPORTED_TASKS_LITERAL
from kvasir_research.agents.v1.deps import AgentDepsFull


@dataclass(kw_only=True)
class AnalysisDeps(AgentDepsFull):
    data_paths: List[str]
    injected_analyses: List[UUID]
    time_limit: int
    # Key: name, value: (type, content), content is code, markdown, or output
    notebook: OrderedDict[str,
                          Tuple[Literal["code", "markdown", "output"], str]]
    guidelines: List[SUPPORTED_TASKS_LITERAL] = field(default_factory=list)
