import uuid
from dataclasses import dataclass, field
from typing import Optional, List, Callable

from project_server.client import ProjectClient
from project_server.agents.runner_base import StreamedCode
from synesis_schemas.main_server import ModelEntity, DataSource, Dataset, Analysis, Pipeline, Project
from synesis_schemas.project_server import FileInRun, RenamedFile


@dataclass
class SWEAgentDeps:
    bearer_token: str
    container_name: str
    client: ProjectClient
    conversation_id: uuid.UUID
    project: Project
    model_entities_injected: List[ModelEntity] = field(default_factory=list)
    data_sources_injected: List[DataSource] = field(default_factory=list)
    datasets_injected: List[Dataset] = field(default_factory=list)
    analyses_injected: List[Analysis] = field(default_factory=list)
    pipelines_injected: List[Pipeline] = field(default_factory=list)
    new_files: List[FileInRun] = field(default_factory=list)
    modified_files: List[FileInRun] = field(default_factory=list)
    deleted_files: List[FileInRun] = field(default_factory=list)
    renamed_files: List[RenamedFile] = field(default_factory=list)
    log_code: Optional[Callable[StreamedCode, None]] = None
