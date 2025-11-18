import uuid
# , CheckConstraint
from sqlalchemy import Table, Column, String, DateTime, func, ForeignKey
from sqlalchemy.dialects.postgresql import UUID, BYTEA
from synesis_api.database.core import metadata

# General run models

run = Table(
    "run",
    metadata,
    Column("id", UUID(as_uuid=True), primary_key=True, default=uuid.uuid4),
    # Only for user-facing runs, SWE does not need spec
    Column("user_id", UUID(as_uuid=True),
           ForeignKey("auth.users.id"), nullable=False),
    Column("project_id", UUID(as_uuid=True), nullable=True),
    Column("run_name", String, nullable=False),
    Column("description", String, nullable=True),
    Column("configuration_defaults_description", String, nullable=True),
    Column("type", String, nullable=False),
    Column("status", String, nullable=False),
    Column("started_at", DateTime(timezone=True), nullable=False),
    Column("completed_at", DateTime(timezone=True), nullable=True),
    schema="runs"
)


run_message = Table(
    "run_message",
    metadata,
    Column("id", UUID(as_uuid=True), primary_key=True, default=uuid.uuid4),
    Column("content", String, nullable=False),
    Column("run_id", UUID(as_uuid=True),
           ForeignKey("runs.run.id"), nullable=False),
    # tool_call, result, error
    Column("type", String, nullable=True),
    Column("created_at", DateTime(timezone=True),
           nullable=False, default=func.now()),
    schema="runs"
)


run_pydantic_message = Table(
    "run_pydantic_message",
    metadata,
    Column("id", UUID(as_uuid=True), primary_key=True, default=uuid.uuid4),
    Column("run_id", UUID(as_uuid=True),
           ForeignKey("runs.run.id"), nullable=False),
    Column("message_list", BYTEA, nullable=False),
    Column("created_at", DateTime(timezone=True),
           nullable=False, default=func.now()),
    schema="runs"
)


analysis_run = Table(
    "analysis_run",
    metadata,
    Column("run_id", UUID(as_uuid=True),
           ForeignKey("runs.run.id"), nullable=False),
    Column("analysis_id", UUID(as_uuid=True),
           ForeignKey("analysis.analysis.id"), nullable=False),
    # Track what Kvasir run started the analysis run
    Column("kvasir_run_id", UUID(as_uuid=True),
           ForeignKey("runs.kvasir_run.id"), nullable=False),
    Column("created_at", DateTime(timezone=True),
           nullable=False, default=func.now()),
    Column("updated_at", DateTime(timezone=True),
           nullable=False, default=func.now(), onupdate=func.now()),
    schema="runs"
)


pipeline_run = Table(
    "pipeline_run",
    metadata,
    Column("run_id", UUID(as_uuid=True),
           ForeignKey("runs.run.id"), nullable=False),
    Column("pipeline_id", UUID(as_uuid=True),
           ForeignKey("pipeline.pipeline.id"), nullable=False),
    Column("kvasir_run_id", UUID(as_uuid=True),
           ForeignKey("runs.kvasir_run.id"), nullable=False),
    Column("created_at", DateTime(timezone=True),
           nullable=False, default=func.now()),
    Column("updated_at", DateTime(timezone=True),
           nullable=False, default=func.now(), onupdate=func.now()),
    schema="runs"
)


kvasir_run = Table(
    "kvasir_run",
    metadata,
    Column("run_id", UUID(as_uuid=True),
           ForeignKey("runs.run.id"), nullable=False),
    Column("conversation_id", UUID(as_uuid=True),
           ForeignKey("orchestrator.conversation.id"), nullable=False),
    Column("created_at", DateTime(timezone=True),
           nullable=False, default=func.now()),
    Column("updated_at", DateTime(timezone=True),
           nullable=False, default=func.now(), onupdate=func.now()),
    schema="runs"
)
