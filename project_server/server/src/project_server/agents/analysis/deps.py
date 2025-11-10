import uuid
from pydantic_ai.messages import ModelMessage
from dataclasses import dataclass, field
from typing import List

from project_server.client import ProjectClient


@dataclass
class AnalysisDeps:
    client: ProjectClient
    run_id: uuid.UUID
    project_id: uuid.UUID
    analysis_id: uuid.UUID
    container_name: str
    # store full analysis done so far
    analysis_id: uuid.UUID
    model_entities_injected: List[uuid.UUID] = field(default_factory=list)
    analyses_injected: List[uuid.UUID] = field(default_factory=list)
    data_sources_injected: List[uuid.UUID] = field(default_factory=list)
    datasets_injected: List[uuid.UUID] = field(default_factory=list)
    results_generated: bool = False
    helper_history: List[ModelMessage] = field(default_factory=list)
