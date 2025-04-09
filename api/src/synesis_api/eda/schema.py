from pydantic import BaseModel
from uuid import UUID


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
