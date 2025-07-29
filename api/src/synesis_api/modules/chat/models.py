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
    # User, agent
    Column("role", String, nullable=False),
    Column("content", String, nullable=False),
    Column("job_id", UUID(as_uuid=True), nullable=True),
    # tool_call, result, error, chat
    Column("type", String, nullable=True),
    Column("context_id", UUID(as_uuid=True),
           ForeignKey("chat.context.id"), nullable=True),
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
    schema="chat"
)


# Conversation mode stores whether the conversation is in chat, data integration, analysis, or automation mode
# This is so we know whether to launch the agent or update it with the new message
# The mode may change over time, and the most recent created_at mode is the one that is active
conversation_mode = Table(
    "conversation_mode",
    metadata,
    Column("id", UUID(as_uuid=True), primary_key=True, default=uuid.uuid4),
    Column("conversation_id", UUID(as_uuid=True),
           ForeignKey("chat.conversation.id"), nullable=False),
    Column("mode", String, nullable=False),
    Column("created_at", DateTime(timezone=True),
           nullable=False, default=func.now()),
    schema="chat"
)


context = Table(
    "context",
    metadata,
    Column("id", UUID(as_uuid=True), primary_key=True, default=uuid.uuid4),
    schema="chat"
)


data_source_context = Table(
    "data_source_context",
    metadata,
    Column("context_id", UUID(as_uuid=True),
           ForeignKey("chat.context.id"), nullable=False),
    Column("data_source_id", UUID(as_uuid=True),
           ForeignKey("data_integration.data_source.id"), nullable=False),
    PrimaryKeyConstraint("context_id", "data_source_id"),
    schema="chat"
)


dataset_context = Table(
    "dataset_context",
    metadata,
    Column("context_id", UUID(as_uuid=True),
           ForeignKey("chat.context.id"), nullable=False),
    Column("dataset_id", UUID(as_uuid=True),
           ForeignKey("data_objects.dataset.id"), nullable=False),
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
