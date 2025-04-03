from typing import Literal
from datetime import datetime
from ..base_schema import BaseSchema
from ..ontology.schema import TimeSeriesDataset, FeatureDataset
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
