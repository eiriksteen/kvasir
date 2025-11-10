import uuid
from dataclasses import dataclass, field
from typing import List, Callable, Literal

from project_server.client import ProjectClient
from synesis_schemas.main_server import Project, Dataset


@dataclass
class ExtractionDeps:
    container_name: str
    project: Project
    client: ProjectClient
    run_id: uuid.UUID
    bearer_token: str
    created_datasets: List[Dataset] = field(default_factory=list)
    object_groups_with_charts: List[uuid.UUID] = field(default_factory=list)
    initial_submission_callback: Callable[[], None] = None
    log_message: Callable[[str, Literal["tool_call", "result", "error"]], None] = field(
        default_factory=lambda: lambda content, type: None)
