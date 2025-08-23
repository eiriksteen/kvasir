from typing import Literal, List, Optional, Union
from datetime import datetime, timezone
import uuid
from synesis_api.base_schema import BaseSchema
from synesis_api.modules.data_sources.schema import DataSource


# DB Models

class RunInDB(BaseSchema):
    id: uuid.UUID
    user_id: uuid.UUID
    conversation_id: uuid.UUID
    type: Literal["data_integration", "analysis", "pipeline", "swe"]
    status: str
    started_at: datetime
    parent_run_id: Optional[uuid.UUID] = None
    completed_at: Optional[datetime] = None
    run_name: Optional[str] = None


class RunMessageInDB(BaseSchema):
    id: uuid.UUID
    content: str
    run_id: uuid.UUID
    type:  Literal["tool_call", "result", "error"]
    created_at: datetime = datetime.now(timezone.utc)


class RunPydanticMessageInDB(BaseSchema):
    id: uuid.UUID
    run_id: uuid.UUID
    message_list: bytes
    created_at: datetime = datetime.now(timezone.utc)


class DataSourceInIntegrationRunInDB(BaseSchema):
    run_id: uuid.UUID
    data_source_id: uuid.UUID
    created_at: datetime


class DataIntegrationRunInputInDB(BaseSchema):
    run_id: uuid.UUID
    target_dataset_description: str
    created_at: datetime
    updated_at: datetime


class ModelIntegrationRunInputInDB(BaseSchema):
    run_id: uuid.UUID
    model_id_str: str
    source: Literal["github", "pip", "source_code"]


class DataIntegrationRunResultInDB(BaseSchema):
    run_id: uuid.UUID
    dataset_id: uuid.UUID
    code_explanation: str
    python_code_path: str


class ModelIntegrationRunResultInDB(BaseSchema):
    run_id: uuid.UUID
    model_id: uuid.UUID


# API Models


class DataIntegrationRunInput(BaseSchema):
    run_id: uuid.UUID
    target_dataset_description: str
    data_source_ids: List[uuid.UUID] = []


RunInput = Union[DataIntegrationRunInput, ModelIntegrationRunInputInDB]
RunResult = Union[DataIntegrationRunResultInDB, ModelIntegrationRunResultInDB]


class Run(RunInDB):
    input: Optional[RunInput] = None
    result: Optional[RunResult] = None
