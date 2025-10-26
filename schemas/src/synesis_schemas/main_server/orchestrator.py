import uuid
from typing import Literal, List, Optional
from datetime import datetime, timezone
from pydantic import BaseModel, field_validator
from .code import script_type_literal


# DB Models


class ConversationInDB(BaseModel):
    id: uuid.UUID
    user_id: uuid.UUID
    name: str
    project_id: uuid.UUID
    created_at: datetime = datetime.now(timezone.utc)


class RunInConversationInDB(BaseModel):
    conversation_id: uuid.UUID
    run_id: uuid.UUID
    context_id: Optional[uuid.UUID] = None
    created_at: datetime = datetime.now(timezone.utc)


class ChatMessageInDB(BaseModel):
    id: uuid.UUID
    content: str
    conversation_id: uuid.UUID
    role: Literal["user", "assistant"]
    type: Literal["tool_call", "chat"]
    context_id: Optional[uuid.UUID] = None
    created_at: datetime = datetime.now(timezone.utc)


class ChatPydanticMessageInDB(BaseModel):
    id: uuid.UUID
    conversation_id: uuid.UUID
    message_list: bytes
    created_at: datetime = datetime.now(timezone.utc)


class ContextInDB(BaseModel):
    id: uuid.UUID


class DataSourceContextInDB(BaseModel):
    context_id: uuid.UUID
    data_source_id: uuid.UUID


class DatasetContextInDB(BaseModel):
    context_id: uuid.UUID
    dataset_id: uuid.UUID


class ModelEntityContextInDB(BaseModel):
    context_id: uuid.UUID
    model_entity_id: uuid.UUID


class PipelineContextInDB(BaseModel):
    context_id: uuid.UUID
    pipeline_id: uuid.UUID


class AnalysisContextInDB(BaseModel):
    context_id: uuid.UUID
    analysis_id: uuid.UUID


# API Models


class Context(BaseModel):
    id: uuid.UUID
    data_source_ids: List[uuid.UUID] = []
    dataset_ids: List[uuid.UUID] = []
    pipeline_ids: List[uuid.UUID] = []
    analysis_ids: List[uuid.UUID] = []
    model_entity_ids: List[uuid.UUID] = []


class ChatMessage(ChatMessageInDB):
    context: Optional[Context] = None


class SetupImplementation(BaseModel):
    dependencies: List[str]
    python_version: str
    script: str


class NewScript(BaseModel):
    filename: str
    script: str


class ModifiedScript(BaseModel):
    original_filename: str
    new_filename: str
    original_script: str
    new_script: str
    type: script_type_literal


class Implementation(BaseModel):
    conversation_id: uuid.UUID
    main_script: NewScript
    run_output: str
    new_scripts: List[NewScript] = []
    modified_scripts: List[ModifiedScript] = []


class SWEResult(BaseModel):
    conversation_id: uuid.UUID
    implementation: Implementation
    setup: Optional[SetupImplementation] = None


class ImplementationApprovalResponse(BaseModel):
    approved: bool
    feedback: Optional[str] = None

    @field_validator('feedback')
    @classmethod
    def validate_feedback_when_not_approved(cls, v, info):
        if not info.data.get('approved', True) and v is None:
            raise ValueError('Feedback is required when approved is False')
        return v

# Create Models


class ContextCreate(BaseModel):
    data_source_ids: List[uuid.UUID] = []
    dataset_ids: List[uuid.UUID] = []
    pipeline_ids: List[uuid.UUID] = []
    analysis_ids: List[uuid.UUID] = []
    model_entity_ids: List[uuid.UUID] = []


class UserChatMessageCreate(BaseModel):
    content: str
    conversation_id: uuid.UUID
    context: Optional[ContextCreate] = None
    save_to_db: bool = True


class ConversationCreate(BaseModel):
    project_id: uuid.UUID
