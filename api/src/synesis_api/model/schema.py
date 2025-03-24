from pydantic import BaseModel
from datetime import datetime
from uuid import UUID

class ModelJobMetadata(BaseModel):
    id: UUID
    status: str
    started_at: datetime
    completed_at: datetime | None = None

class ModelJobMetadataInDB(ModelJobMetadata):
    user_id: UUID
    api_key_id: UUID

class ModelJobResult(BaseModel):
    job_id: UUID

class ModelJobResultInDB(ModelJobResult):
    python_code: str


class ModelAgentOutput(BaseModel):
    explanation: str
    python_code: str