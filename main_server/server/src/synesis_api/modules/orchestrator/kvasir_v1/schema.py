import uuid
from typing import Literal, List
from datetime import datetime
from pydantic import BaseModel


# DB Schemas

DEP_TYPE_LITERAL = Literal["swe", "analysis", "orchestrator"]
RESULT_TYPE_LITERAL = Literal["swe", "analysis"]


class ResultsQueueInDB(BaseModel):
    id: uuid.UUID
    run_id: uuid.UUID
    content: List[str]
    created_at: datetime


class DepsInDB(BaseModel):
    id: uuid.UUID
    run_id: uuid.UUID
    type: DEP_TYPE_LITERAL
    content: str
    created_at: datetime


class ResultInDB(BaseModel):
    id: uuid.UUID
    run_id: uuid.UUID
    type: RESULT_TYPE_LITERAL
    content: str
    created_at: datetime


class PydanticAIMessageInDB(BaseModel):
    id: uuid.UUID
    run_id: uuid.UUID
    message_list: bytes
    created_at: datetime


# Create Schemas

class ResultsQueueCreate(BaseModel):
    run_id: uuid.UUID
    content: List[str]


class DepsCreate(BaseModel):
    run_id: uuid.UUID
    type: DEP_TYPE_LITERAL
    content: str


class ResultCreate(BaseModel):
    run_id: uuid.UUID
    type: RESULT_TYPE_LITERAL
    content: str


class PydanticAIMessageCreate(BaseModel):
    run_id: uuid.UUID
    content: bytes
