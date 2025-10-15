import uuid
from dataclasses import dataclass


@dataclass
class OrchestratorAgentDeps:
    user_id: uuid.UUID
    project_id: uuid.UUID
    conversation_id: uuid.UUID
