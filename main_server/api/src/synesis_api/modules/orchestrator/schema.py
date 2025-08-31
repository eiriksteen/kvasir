from typing import Literal, List, Optional
from datetime import datetime, timezone
from synesis_api.base_schema import BaseSchema
from pydantic import model_validator
import uuid


# DB Models


class ConversationInDB(BaseSchema):
    id: uuid.UUID
    user_id: uuid.UUID
    name: str
    project_id: uuid.UUID
    created_at: datetime = datetime.now(timezone.utc)


class RunInConversationInDB(BaseSchema):
    conversation_id: uuid.UUID
    run_id: uuid.UUID
    context_id: Optional[uuid.UUID] = None
    created_at: datetime = datetime.now(timezone.utc)


class ChatMessageInDB(BaseSchema):
    id: uuid.UUID
    content: str
    conversation_id: uuid.UUID
    role: Literal["user", "assistant"]
    context_id: Optional[uuid.UUID] = None
    created_at: datetime = datetime.now(timezone.utc)


class ChatPydanticMessageInDB(BaseSchema):
    id: uuid.UUID
    conversation_id: uuid.UUID
    message_list: bytes
    created_at: datetime = datetime.now(timezone.utc)


class ContextInDB(BaseSchema):
    id: uuid.UUID


class DataSourceContextInDB(BaseSchema):
    context_id: uuid.UUID
    data_source_id: uuid.UUID


class DatasetContextInDB(BaseSchema):
    context_id: uuid.UUID
    dataset_id: uuid.UUID


class PipelineContextInDB(BaseSchema):
    context_id: uuid.UUID
    pipeline_id: uuid.UUID


class AnalysisContextInDB(BaseSchema):
    context_id: uuid.UUID
    analysis_id: uuid.UUID


# API Models


class Context(BaseSchema):
    id: uuid.UUID
    data_source_ids: List[uuid.UUID] = []
    dataset_ids: List[uuid.UUID] = []
    pipeline_ids: List[uuid.UUID] = []
    analysis_ids: List[uuid.UUID] = []


class ChatMessage(ChatMessageInDB):
    context: Optional[Context] = None


# Create Models


class ContextCreate(BaseSchema):
    data_source_ids: List[uuid.UUID] = []
    dataset_ids: List[uuid.UUID] = []
    pipeline_ids: List[uuid.UUID] = []
    analysis_ids: List[uuid.UUID] = []


class UserChatMessageCreate(BaseSchema):
    content: str
    conversation_id: uuid.UUID
    context: Optional[ContextCreate] = None


class ConversationCreate(BaseSchema):
    project_id: uuid.UUID
