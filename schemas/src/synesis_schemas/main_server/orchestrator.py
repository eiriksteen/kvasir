import uuid
from typing import Literal, List, Optional
from datetime import datetime, timezone
from pydantic import BaseModel


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


class DataSourceInGraph(BaseModel):
    id: uuid.UUID
    name: str
    type: Literal["file"]
    brief_description: str
    to_datasets: List[uuid.UUID] = []
    to_analyses: List[uuid.UUID] = []


class DatasetInGraph(BaseModel):
    id: uuid.UUID
    name: str
    brief_description: str
    to_pipelines: List[uuid.UUID] = []
    to_analyses: List[uuid.UUID] = []
    from_data_sources: List[uuid.UUID] = []
    from_datasets: List[uuid.UUID] = []
    from_pipelines: List[uuid.UUID] = []


class PipelineInGraph(BaseModel):
    id: uuid.UUID
    name: str
    brief_description: str
    from_datasets: List[uuid.UUID] = []
    from_model_entities: List[uuid.UUID] = []
    to_datasets: List[uuid.UUID] = []
    to_model_entities: List[uuid.UUID] = []


class AnalysisInGraph(BaseModel):
    id: uuid.UUID
    name: str
    brief_description: str
    from_datasets: List[uuid.UUID] = []
    from_data_sources: List[uuid.UUID] = []


class ModelEntityInGraph(BaseModel):
    id: uuid.UUID
    name: str
    brief_description: str
    to_pipelines: List[uuid.UUID] = []


class ProjectGraph(BaseModel):
    data_sources: List[DataSourceInGraph] = []
    datasets: List[DatasetInGraph] = []
    pipelines: List[PipelineInGraph] = []
    analyses: List[AnalysisInGraph] = []
    model_entities: List[ModelEntityInGraph] = []


# Create Models


class ContextCreate(BaseModel):
    data_source_ids: List[uuid.UUID] = []
    dataset_ids: List[uuid.UUID] = []
    pipeline_ids: List[uuid.UUID] = []
    analysis_ids: List[uuid.UUID] = []
    model_entity_ids: List[uuid.UUID] = []


class CreationSettings(BaseModel):
    public: bool


class UserChatMessageCreate(BaseModel):
    content: str
    conversation_id: uuid.UUID
    context: Optional[ContextCreate] = None
    creation_settings: Optional[CreationSettings] = None


class ConversationCreate(BaseModel):
    project_id: uuid.UUID
