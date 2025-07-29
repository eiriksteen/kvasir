from typing import Literal, List, Optional
from datetime import datetime, timezone
from synesis_api.base_schema import BaseSchema
import uuid


# DB Models


class ChatMessageInDB(BaseSchema):
    id: uuid.UUID
    content: str
    conversation_id: uuid.UUID
    role: Literal["user", "agent"]
    type: Literal["tool_call", "result", "error", "chat"]
    job_id: Optional[uuid.UUID] = None
    context_id: Optional[uuid.UUID] = None
    created_at: datetime = datetime.now(timezone.utc)


class PydanticMessageInDB(BaseSchema):
    id: uuid.UUID
    conversation_id: uuid.UUID
    message_list: bytes
    created_at: datetime = datetime.now(timezone.utc)


class ConversationInDB(BaseSchema):
    id: uuid.UUID
    user_id: uuid.UUID
    name: str
    project_id: uuid.UUID
    created_at: datetime = datetime.now(timezone.utc)


class ConversationModeInDB(BaseSchema):
    id: uuid.UUID
    conversation_id: uuid.UUID
    mode: Literal["chat", "data_integration", "analysis", "automation"]
    created_at: datetime = datetime.now(timezone.utc)


class ContextInDB(BaseSchema):
    id: uuid.UUID


class DataSourceContextInDB(BaseSchema):
    context_id: uuid.UUID
    data_source_id: uuid.UUID


class DatasetContextInDB(BaseSchema):
    context_id: uuid.UUID
    dataset_id: uuid.UUID


class AutomationContextInDB(BaseSchema):
    context_id: uuid.UUID
    automation_id: uuid.UUID


class AnalysisContextInDB(BaseSchema):
    context_id: uuid.UUID
    analysis_id: uuid.UUID


# API Models


class Context(BaseSchema):
    id: uuid.UUID
    data_source_ids: List[uuid.UUID] = []
    dataset_ids: List[uuid.UUID] = []
    automation_ids: List[uuid.UUID] = []
    analysis_ids: List[uuid.UUID] = []


class ChatMessage(BaseSchema):
    id: uuid.UUID
    content: str
    conversation_id: uuid.UUID
    role: Literal["user", "agent"]
    type: Literal["tool_call", "result", "error", "chat"]
    job_id: Optional[uuid.UUID] = None
    context: Optional[Context] = None
    created_at: datetime


class Conversation(BaseSchema):
    id: uuid.UUID
    user_id: uuid.UUID
    project_id: uuid.UUID
    name: str
    created_at: datetime = datetime.now(timezone.utc)
    mode: Literal["chat", "data_integration", "analysis", "automation"]


class ConversationWithMessages(BaseSchema):
    id: uuid.UUID
    user_id: uuid.UUID
    project_id: uuid.UUID
    name: str
    created_at: datetime = datetime.now(timezone.utc)
    mode: Literal["chat", "data_integration", "analysis", "automation"]
    messages: List[ChatMessage]


# Create Models


class ContextCreate(BaseSchema):
    data_source_ids: List[uuid.UUID] = []
    dataset_ids: List[uuid.UUID] = []
    automation_ids: List[uuid.UUID] = []
    analysis_ids: List[uuid.UUID] = []


class UserChatMessageCreate(BaseSchema):
    message_id: uuid.UUID
    conversation_id: uuid.UUID
    content: str
    context: Optional[ContextCreate] = None


class ConversationCreate(BaseSchema):
    project_id: uuid.UUID
    content: str
