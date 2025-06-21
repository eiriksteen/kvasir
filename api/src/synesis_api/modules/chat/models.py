import uuid
from sqlalchemy import Table, Column, String, DateTime, func, ForeignKey, PrimaryKeyConstraint
from sqlalchemy.dialects.postgresql import UUID, BYTEA
from synesis_api.database.core import metadata


chat_message = Table(
    "chat_message",
    metadata,
    Column("id", UUID(as_uuid=True), primary_key=True, default=uuid.uuid4),
    Column("conversation_id", UUID(as_uuid=True),
           ForeignKey("chat.conversation.id"), nullable=False),
    Column("role", String, nullable=False),
    Column("content", String, nullable=False),
    Column("created_at", DateTime(timezone=True),
           nullable=False, default=func.now()),
    schema="chat"
)


pydantic_message = Table(
    "pydantic_message",
    metadata,
    Column("id", UUID(as_uuid=True), primary_key=True, default=uuid.uuid4),
    Column("conversation_id", UUID(as_uuid=True),
           ForeignKey("chat.conversation.id"), nullable=False),
    Column("message_list", BYTEA, nullable=False),
    Column("created_at", DateTime(timezone=True),
           nullable=False, default=func.now()),
    schema="chat"
)


conversations = Table(
    "conversation",
    metadata,
    Column("id", UUID(as_uuid=True), primary_key=True, default=uuid.uuid4),
    Column("user_id", UUID(as_uuid=True),
           ForeignKey("auth.users.id"), nullable=False),
    schema="chat"
)

context = Table(
    "context",
    metadata,
    Column("id", UUID(as_uuid=True), primary_key=True, default=uuid.uuid4),
    Column("conversation_id", UUID(as_uuid=True),
           ForeignKey("chat.conversation.id"), nullable=False),
    Column("created_at", DateTime(timezone=True),
           nullable=False, default=func.now()),
    schema="chat"
)

dataset_context = Table(
    "dataset_context",
    metadata,
    Column("context_id", UUID(as_uuid=True),
           ForeignKey("chat.context.id"), nullable=False),
    Column("dataset_id", UUID(as_uuid=True),
           ForeignKey("ontology.dataset.id"), nullable=False),
    PrimaryKeyConstraint("context_id", "dataset_id"),
    schema="chat"
)

automation_context = Table(
    "automation_context",
    metadata,
    Column("context_id", UUID(as_uuid=True),
           ForeignKey("chat.context.id"), nullable=False),
    Column("automation_id", UUID(as_uuid=True),
           ForeignKey("automation.automation.id"), nullable=False),
    PrimaryKeyConstraint("context_id", "automation_id"),
    schema="chat"
)

analysis_context = Table(
    "analysis_context",
    metadata,
    Column("context_id", UUID(as_uuid=True),
           ForeignKey("chat.context.id"), nullable=False),
    Column("analysis_id", UUID(as_uuid=True),
           ForeignKey("analysis.analysis_jobs_results.job_id"), nullable=False),
    PrimaryKeyConstraint("context_id", "analysis_id"),
    schema="chat"
)
