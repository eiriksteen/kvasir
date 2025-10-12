from dataclasses import dataclass
from project_server.client import ProjectClient


@dataclass
class ModelIntegrationAgentDeps:
    client: ProjectClient
