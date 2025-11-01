import uuid
from dataclasses import dataclass

from project_server.client import ProjectClient
from synesis_schemas.main_server import Project


@dataclass
class ExtractionDeps:
    container_name: str
    project: Project
    client: ProjectClient
    run_id: uuid.UUID
    bearer_token: str
