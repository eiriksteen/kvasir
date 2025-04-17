from typing import Literal, List
from datetime import datetime
from ...base_schema import BaseSchema
from ..ontology.schema import Datasets
from ..automation.schema import Automations
import uuid


class ChatbotOutput(BaseSchema):
    goal_description: str
    deliverable_description: str
    task_type: Literal["analysis", "automation"]


class ChatMessage(BaseSchema):
    id: uuid.UUID
    conversation_id: uuid.UUID
    role: Literal["user", "assistant"]
    content: str
    created_at: datetime


class Prompt(BaseSchema):
    content: str


class Conversation(BaseSchema):
    id: uuid.UUID
    user_id: uuid.UUID


class PydanticMessage(BaseSchema):
    id: uuid.UUID
    conversation_id: uuid.UUID
    message_list: bytes
    created_at: datetime


class ContextCreate(BaseSchema):
    conversation_id: uuid.UUID
    dataset_ids: List[uuid.UUID] = []
    automation_ids: List[uuid.UUID] = []


class Context(BaseSchema):
    id: uuid.UUID
    conversation_id: uuid.UUID
    created_at: datetime
    dataset_ids: List[uuid.UUID] = []
    automation_ids: List[uuid.UUID] = []


class ContextInDB(BaseSchema):
    id: uuid.UUID
    conversation_id: uuid.UUID
    created_at: datetime


class DatasetContextInDB(BaseSchema):
    context_id: uuid.UUID
    dataset_id: uuid.UUID


class AutomationContextInDB(BaseSchema):
    context_id: uuid.UUID
    automation_id: uuid.UUID
