from pydantic import BaseModel
from datetime import datetime, timezone
from uuid import UUID
from synesis_api.base_schema import BaseSchema


class ModelJobResult(BaseSchema):
    job_id: UUID
    explanation: str
    python_code: str


class ModelJobResultInDB(ModelJobResult):
    pass


class ModelAgentOutput(BaseSchema):
    explanation: str
    python_code: str


class Automations(BaseSchema):
    id: UUID
    name: str
    description: str
    created_at: datetime = datetime.now(timezone.utc)
    updated_at: datetime = datetime.now(timezone.utc)
