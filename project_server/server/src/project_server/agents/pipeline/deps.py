from dataclasses import dataclass
from project_server.client import ProjectClient


@dataclass
class PipelineAgentDeps:
    client: ProjectClient
