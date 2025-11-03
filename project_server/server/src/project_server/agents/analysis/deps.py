import uuid
from dataclasses import dataclass, field
from typing import List

from project_server.client import ProjectClient


@dataclass
class AnalysisDeps:
    client: ProjectClient
    run_id: uuid.UUID
    project_id: uuid.UUID
    analysis_id: uuid.UUID
    results_generated: bool = False
    model_entities_injected: List[uuid.UUID] = field(default_factory=list)
    analyses_injected: List[uuid.UUID] = field(default_factory=list)
    data_sources_injected: List[uuid.UUID] = field(default_factory=list)
    datasets_injected: List[uuid.UUID] = field(default_factory=list)
