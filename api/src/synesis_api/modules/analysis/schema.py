from pydantic import BaseModel
from uuid import UUID


class EDAJobResult(BaseModel):
    job_id: UUID
    basic_eda: str | None = None
    advanced_eda: str | None = None
    independent_eda: str | None = None
    python_code: str | None = None
    ad_hoc: str | None = None


class EDAJobResultInDB(EDAJobResult):
    dataset_id: UUID


class EDAResponse(BaseModel):
    analysis: str


class EDAResponseWithCode(EDAResponse):
    python_code: str

class EDAResponseTotal(BaseModel):
    basic_eda: str
    advanced_eda: str
    independent_eda: str
    python_code: str


class EDAResponseSummary(BaseModel):
    summary: str
    python_code: str
