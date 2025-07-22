from typing import Literal, List, Optional
from datetime import datetime, timezone
from synesis_api.base_schema import BaseSchema
import uuid


class Context(BaseSchema):
    # Should this be optional?
    id: Optional[uuid.UUID] = None
    project_id: uuid.UUID
    data_source_ids: List[uuid.UUID] = []
    dataset_ids: List[uuid.UUID] = []
    automation_ids: List[uuid.UUID] = []
    analysis_ids: List[uuid.UUID] = []


class ChatMessageInDB(BaseSchema):
    id: uuid.UUID
    content: str
    conversation_id: uuid.UUID
    role: Literal["user", "agent"]
    type: Literal["tool_call", "result", "error", "chat"]
    job_id: Optional[uuid.UUID] = None
    context_id: Optional[uuid.UUID] = None
    created_at: datetime = datetime.now(timezone.utc)


class ChatMessage(BaseSchema):
    id: uuid.UUID
    content: str
    conversation_id: uuid.UUID
    role: Literal["user", "agent"]
    type: Literal["tool_call", "result", "error", "chat"]
    job_id: Optional[uuid.UUID] = None
    context: Optional[Context] = None
    created_at: datetime


class Prompt(BaseSchema):
    conversation_id: uuid.UUID
    context: Optional[Context] = None
    content: str


class ConversationCreate(BaseSchema):
    project_id: uuid.UUID
    content: str


class ConversationInDB(BaseSchema):
    id: uuid.UUID
    user_id: uuid.UUID
    name: str
    project_id: uuid.UUID
    created_at: datetime = datetime.now(timezone.utc)


class Conversation(BaseSchema):
    id: uuid.UUID
    user_id: uuid.UUID
    project_id: uuid.UUID
    name: str
    created_at: datetime = datetime.now(timezone.utc)
    messages: List[ChatMessage]


class PydanticMessage(BaseSchema):
    id: uuid.UUID
    conversation_id: uuid.UUID
    message_list: bytes
    created_at: datetime = datetime.now(timezone.utc)


class ContextInDB(BaseSchema):
    id: uuid.UUID
    project_id: uuid.UUID


class DatasetContextInDB(BaseSchema):
    context_id: uuid.UUID
    dataset_id: uuid.UUID


class AutomationContextInDB(BaseSchema):
    context_id: uuid.UUID
    automation_id: uuid.UUID


class AnalysisContextInDB(BaseSchema):
    context_id: uuid.UUID
    analysis_id: uuid.UUID


class ConversationModeInDB(BaseSchema):
    id: uuid.UUID
    conversation_id: uuid.UUID
    mode: Literal["chat", "data_integration", "analysis", "automation"]
    created_at: datetime = datetime.now(timezone.utc)
