from pydantic import BaseModel
from datetime import datetime
from uuid import UUID
from ...base_schema import BaseSchema


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
    created_at: datetime
    updated_at: datetime
