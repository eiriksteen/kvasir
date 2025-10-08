import uuid
from dataclasses import dataclass


@dataclass
class OrchestatorAgentDeps:
    user_id: uuid.UUID
    project_id: uuid.UUID
