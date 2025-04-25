from typing import Literal, List
from datetime import datetime, timezone
from synesis_api.base_schema import BaseSchema
from synesis_api.modules.ontology.schema import Datasets
from synesis_api.modules.automation.schema import Automations
import uuid
from ...auth.schema import User

class ChatbotOutput(BaseSchema):
    goal_description: str
    deliverable_description: str
    task_type: Literal["analysis", "automation"]


class ChatMessage(BaseSchema):
    id: uuid.UUID
    conversation_id: uuid.UUID
    role: Literal["user", "assistant"]
    content: str
    created_at: datetime = datetime.now(timezone.utc)


class Prompt(BaseSchema):
    content: str


class Conversation(BaseSchema):
    id: uuid.UUID
    user_id: uuid.UUID


class PydanticMessage(BaseSchema):
    id: uuid.UUID
    conversation_id: uuid.UUID
    message_list: bytes
    created_at: datetime = datetime.now(timezone.utc)


class ContextCreate(BaseSchema):
    conversation_id: uuid.UUID
    dataset_ids: List[uuid.UUID] = []
    automation_ids: List[uuid.UUID] = []
    analysis_ids: List[uuid.UUID] = []
    append: bool = True
    remove: bool = False


class Context(BaseSchema):
    id: uuid.UUID
    conversation_id: uuid.UUID
    created_at: datetime = datetime.now(timezone.utc)
    dataset_ids: List[uuid.UUID] = []
    automation_ids: List[uuid.UUID] = []
    analysis_ids: List[uuid.UUID] = []

class ContextDeps(Context):
    user: User

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

class AnalysisContextInDB(BaseSchema):
    context_id: uuid.UUID
    analysis_id: uuid.UUID
