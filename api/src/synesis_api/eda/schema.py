from pydantic import BaseModel
from uuid import UUID
from datetime import datetime


class EDAJobMetaData(BaseModel):
    id: UUID
    status: str
    started_at: datetime
    completed_at: datetime | None = None

class EDAJobMetaDataInDB(EDAJobMetaData):
    user_id: UUID
    api_key_id: UUID

class EDAJobResult(BaseModel):
    job_id: UUID
    detailed_summary: str
    python_code: str

class EDAJobResultInDB(EDAJobResult):
    pass

class EDAResponse(BaseModel):
    detailed_summary: str

class EDAResponseWithCode(EDAResponse):
    python_code: str


