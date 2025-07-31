from typing import Literal, List, Optional
from datetime import datetime, timezone
import uuid
from synesis_api.base_schema import BaseSchema
from synesis_api.modules.data_sources.schema import DataSource


# DB Models

class RunInDB(BaseSchema):
    id: uuid.UUID
    type: str
    status: str
    user_id: uuid.UUID
    started_at: datetime
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


class DataSourceInRunInDB(BaseSchema):
    run_id: uuid.UUID
    data_source_id: uuid.UUID
    created_at: datetime


class DataIntegrationRunInputInDB(BaseSchema):
    run_id: uuid.UUID
    target_dataset_description: str
    created_at: datetime
    updated_at: datetime


class DataIntegrationRunResultInDB(BaseSchema):
    run_id: uuid.UUID
    dataset_id: uuid.UUID
    code_explanation: str
    python_code_path: str


class ModelIntegrationRunInputInDB(BaseSchema):
    model_id_str: str
    source: Literal["github", "pip", "source_code"]


class ModelIntegrationRunResultInDB(BaseSchema):
    run_id: uuid.UUID
    model_id: uuid.UUID


# API Models


class DataIntegrationRunInput(DataIntegrationRunInputInDB):
    data_sources: List[DataSource]
