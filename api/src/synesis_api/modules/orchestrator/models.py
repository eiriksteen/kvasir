import uuid
from sqlalchemy import Table, Column, String, DateTime, func, ForeignKey, PrimaryKeyConstraint
from sqlalchemy.dialects.postgresql import UUID, BYTEA
from synesis_api.database.core import metadata


conversation = Table(
    "conversation",
    metadata,
    Column("id", UUID(as_uuid=True), primary_key=True, default=uuid.uuid4),
    Column("user_id", UUID(as_uuid=True),
           ForeignKey("auth.users.id"), nullable=False),
    Column("project_id", UUID(as_uuid=True),
           ForeignKey("project.project.id"), nullable=False),
    Column("name", String, nullable=False),
    Column("created_at", DateTime(timezone=True),
           nullable=False, default=func.now()),
    schema="orchestrator"
)


chat_message = Table(
    "chat_message",
    metadata,
    Column("id", UUID(as_uuid=True), primary_key=True, default=uuid.uuid4),
    Column("conversation_id", UUID(as_uuid=True),
           ForeignKey("orchestrator.conversation.id"), nullable=False),
    # User, assistant
    Column("role", String, nullable=False),
    Column("content", String, nullable=False),
    Column("context_id", UUID(as_uuid=True),
           ForeignKey("orchestrator.chat_context.id"), nullable=True),
    Column("created_at", DateTime(timezone=True),
           nullable=False, default=func.now()),
    schema="orchestrator"
)


chat_pydantic_message = Table(
    "chat_pydantic_message",
    metadata,
    Column("id", UUID(as_uuid=True), primary_key=True, default=uuid.uuid4),
    Column("conversation_id", UUID(as_uuid=True),
           ForeignKey("orchestrator.conversation.id"), nullable=False),
    Column("message_list", BYTEA, nullable=False),
    Column("created_at", DateTime(timezone=True),
           nullable=False, default=func.now()),
    schema="orchestrator"
)


chat_context = Table(
    "chat_context",
    metadata,
    Column("id", UUID(as_uuid=True), primary_key=True, default=uuid.uuid4),
    schema="orchestrator"
)


data_source_context = Table(
    "data_source_context",
    metadata,
    Column("context_id", UUID(as_uuid=True),
           ForeignKey("orchestrator.chat_context.id"), nullable=False),
    Column("data_source_id", UUID(as_uuid=True),
           ForeignKey("data_sources.data_source.id"), nullable=False),
    PrimaryKeyConstraint("context_id", "data_source_id"),
    schema="orchestrator"
)


dataset_context = Table(
    "dataset_context",
    metadata,
    Column("context_id", UUID(as_uuid=True),
           ForeignKey("orchestrator.chat_context.id"), nullable=False),
    Column("dataset_id", UUID(as_uuid=True),
           ForeignKey("data_objects.dataset.id"), nullable=False),
    PrimaryKeyConstraint("context_id", "dataset_id"),
    schema="orchestrator"
)


automation_context = Table(
    "automation_context",
    metadata,
    Column("context_id", UUID(as_uuid=True),
           ForeignKey("orchestrator.chat_context.id"), nullable=False),
    Column("automation_id", UUID(as_uuid=True),
           ForeignKey("automation.automation.id"), nullable=False),
    PrimaryKeyConstraint("context_id", "automation_id"),
    schema="orchestrator"
)


analysis_context = Table(
    "analysis_context",
    metadata,
    Column("context_id", UUID(as_uuid=True),
           ForeignKey("orchestrator.chat_context.id"), nullable=False),
    Column("analysis_id", UUID(as_uuid=True),
           ForeignKey("analysis.analysis_jobs_results.job_id"), nullable=False),
    PrimaryKeyConstraint("context_id", "analysis_id"),
    schema="orchestrator"
)
