import uuid
from dataclasses import dataclass

from project_server.client import ProjectClient


@dataclass
class ExtractionDeps:
    client: ProjectClient
    run_id: uuid.UUID
    project_id: uuid.UUID
