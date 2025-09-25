from uuid import UUID
from typing import Literal, Union, List, Dict
from datetime import datetime
from pydantic import BaseModel

SUPPORTED_MODEL_SOURCES = ["github", "pypi", "gitlab", "huggingface", "local"]
SUPPORTED_MODEL_SOURCES_TYPE = Literal["github",
                                       "pypi", "gitlab", "huggingface", "local"]


# DB Schemas

class ModelSourceInDB(BaseModel):
    id: UUID
    user_id: UUID
    public: bool
    type: SUPPORTED_MODEL_SOURCES_TYPE
    name: str
    description: str
    embedding: List[float]
    created_at: datetime
    updated_at: datetime


class PypiModelSourceInDB(BaseModel):
    id: UUID
    package_name: str
    package_version: str
    created_at: datetime
    updated_at: datetime

# API Schemas


class ModelSourceWithoutEmbedding(ModelSourceInDB):
    id: UUID
    user_id: UUID
    public: bool
    type: SUPPORTED_MODEL_SOURCES_TYPE
    name: str
    description: str
    created_at: datetime
    updated_at: datetime


class PypiModelSourceFull(ModelSourceWithoutEmbedding, PypiModelSourceInDB):
    pass


ModelSource = Union[PypiModelSourceFull]


class ModelSourceBare(BaseModel):
    id: UUID
    name: str
    description: str
    type: SUPPORTED_MODEL_SOURCES_TYPE


# Create Schemas

class BaseModelSourceCreate(BaseModel):
    public: bool
    type: SUPPORTED_MODEL_SOURCES_TYPE
    description: str
    name: str


class PypiModelSourceCreate(BaseModelSourceCreate):
    package_name: str
    package_version: str
    type: Literal["pypi"] = "pypi"


ModelSourceCreate = Union[PypiModelSourceCreate]


MODEL_SOURCE_TYPE_TO_MODEL_SOURCE_CLASS: Dict[SUPPORTED_MODEL_SOURCES, ModelSource] = {
    "pypi": PypiModelSourceFull,
}
