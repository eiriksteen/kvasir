import uuid
from dataclasses import dataclass, field
from typing import List

from project_server.client import ProjectClient
from synesis_schemas.main_server import ModelEntity, DataSource, Dataset, Analysis


@dataclass
class AnalysisDeps:
    client: ProjectClient
    run_id: uuid.UUID
    project_id: uuid.UUID
    analysis_id: uuid.UUID
    model_entities_injected: List[ModelEntity] = field(default_factory=list)
    analyses_injected: List[Analysis] = field(default_factory=list)
    data_sources_injected: List[DataSource] = field(default_factory=list)
    datasets_injected: List[Dataset] = field(default_factory=list)
