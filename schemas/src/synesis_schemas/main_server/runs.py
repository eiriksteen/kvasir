import uuid
from typing import Literal, List, Optional, Union
from datetime import datetime, timezone
from pydantic import BaseModel


# DB Models

class RunInDB(BaseModel):
    id: uuid.UUID
    user_id: uuid.UUID
    type: Literal["data_integration", "analysis",
                  "pipeline", "swe", "data_source_analysis"]
    status: str
    started_at: datetime
    conversation_id: Optional[uuid.UUID] = None
    parent_run_id: Optional[uuid.UUID] = None
    completed_at: Optional[datetime] = None
    run_name: Optional[str] = None


class RunMessageInDB(BaseModel):
    id: uuid.UUID
    content: str
    run_id: uuid.UUID
    type:  Literal["tool_call", "result", "error"]
    created_at: datetime = datetime.now(timezone.utc)


class RunPydanticMessageInDB(BaseModel):
    id: uuid.UUID
    run_id: uuid.UUID
    message_list: bytes
    created_at: datetime = datetime.now(timezone.utc)


class DataSourceInIntegrationRunInDB(BaseModel):
    run_id: uuid.UUID
    data_source_id: uuid.UUID
    created_at: datetime


class DataIntegrationRunInputInDB(BaseModel):
    run_id: uuid.UUID
    target_dataset_description: str
    created_at: datetime
    updated_at: datetime


class ModelIntegrationRunInputInDB(BaseModel):
    run_id: uuid.UUID
    model_id_str: str
    source: Literal["github", "pip", "source_code"]


class DataIntegrationRunResultInDB(BaseModel):
    run_id: uuid.UUID
    dataset_id: uuid.UUID
    code_explanation: str
    python_code_path: str


class ModelIntegrationRunResultInDB(BaseModel):
    run_id: uuid.UUID
    model_id: uuid.UUID


# API Models


class DataIntegrationRunInput(BaseModel):
    run_id: uuid.UUID
    target_dataset_description: str
    data_source_ids: List[uuid.UUID] = []


RunInput = Union[DataIntegrationRunInput, ModelIntegrationRunInputInDB]
RunResult = Union[DataIntegrationRunResultInDB, ModelIntegrationRunResultInDB]


class Run(RunInDB):
    input: Optional[RunInput] = None
    result: Optional[RunResult] = None


# Create Models

class RunCreate(BaseModel):
    type: Literal["data_integration", "analysis",
                  "pipeline", "swe", "data_source_analysis"]
    conversation_id: Optional[uuid.UUID] = None
    parent_run_id: Optional[uuid.UUID] = None
    run_name: Optional[str] = None


class RunMessageCreate(BaseModel):
    type: Literal["tool_call", "result", "error"]
    content: str
    run_id: uuid.UUID


class RunMessageCreatePydantic(BaseModel):
    content: bytes
    run_id: uuid.UUID


class DataIntegrationRunInputCreate(BaseModel):
    run_id: uuid.UUID
    target_dataset_description: str
    data_source_ids: List[uuid.UUID]


class DataIntegrationRunResultCreate(BaseModel):
    run_id: uuid.UUID
    dataset_id: uuid.UUID
    code_explanation: str
    python_code_path: str


# Update Models

class RunStatusUpdate(BaseModel):
    run_id: uuid.UUID
    status: Literal["running", "completed", "failed"]
