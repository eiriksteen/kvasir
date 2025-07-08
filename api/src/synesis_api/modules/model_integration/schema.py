from uuid import UUID
from typing import Literal, Optional
from datetime import datetime
from pydantic import field_validator
from synesis_api.base_schema import BaseSchema
from datetime import timezone


class ModelIntegrationJobInput(BaseSchema):
    model_id: str
    source: Literal["github", "pip"]


class ModelIntegrationJobResult(BaseSchema):
    job_id: UUID
    model_id: UUID


class ModelIntegrationJobResultInDB(ModelIntegrationJobResult):
    pass


class ModelIntegrationPydanticMessage(BaseSchema):
    id: UUID
    job_id: UUID
    message_list: bytes
    created_at: datetime = datetime.now(timezone.utc)


class ModelIntegrationMessage(BaseSchema):
    id: UUID
    job_id: UUID
    content: str
    stage: Literal["setup",
                   "model_analysis",
                   "implementation_planning",
                   "training",
                   "inference"]
    type: Literal["tool_call", "result"]
    current_task: Optional[Literal["classification",
                                   "regression",
                                   "segmentation",
                                   "forecasting",
                                   "null"]] = "null"
    created_at: datetime = datetime.now(timezone.utc)

    @field_validator("current_task")
    def validate_current_task(cls, v, info):
        if info.data.get("stage") in ["planning", "training", "inference"] and v == "null":
            raise ValueError(
                f"current_task is required for stage {info.data['stage']}")
        return v
