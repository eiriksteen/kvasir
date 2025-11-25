import uuid
from sqlalchemy import Table, Column, String, DateTime, func, ForeignKey
from sqlalchemy.dialects.postgresql import UUID, BYTEA
from kvasir_api.database.core import metadata


# Models specific to Kvasir V1 Agent


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
    schema="kvasir_v1"
)


message = Table(
    "message",
    metadata,
    Column("id", UUID(as_uuid=True), primary_key=True, default=uuid.uuid4),
    Column("content", String, nullable=False),
    Column("run_id", UUID(as_uuid=True),
           ForeignKey("kvasir_v1.run.id"), nullable=False),
    # swe, analysis, kvasir, user
    Column("role", String, nullable=False),
    # tool_call, result, error, info, chat
    Column("type", String, nullable=False),
    Column("created_at", DateTime(timezone=True),
           nullable=False, default=func.now()),
    schema="kvasir_v1"
)


pydantic_ai_message = Table(
    "pydantic_ai_message",
    metadata,
    Column("id", UUID(as_uuid=True), primary_key=True, default=uuid.uuid4),
    Column("run_id", UUID(as_uuid=True),
           ForeignKey("kvasir_v1.run.id"), nullable=False),
    Column("message_list", BYTEA, nullable=False),
    Column("created_at", DateTime(timezone=True),
           nullable=False, default=func.now()),
    schema="kvasir_v1"
)


deps = Table(
    "deps",
    metadata,
    Column("id", UUID(as_uuid=True), primary_key=True, default=uuid.uuid4),
    Column("run_id", UUID(as_uuid=True),
           ForeignKey("kvasir_v1.run.id"), nullable=False),
    # swe, analysis, kvasir
    Column("type", String, nullable=False),
    Column("content", String, nullable=False),
    Column("created_at", DateTime(timezone=True),
           nullable=False, default=func.now()),
    schema="kvasir_v1"
)


analysis_run = Table(
    "analysis_run",
    metadata,
    Column("run_id", UUID(as_uuid=True),
           ForeignKey("kvasir_v1.run.id"),
           primary_key=True,
           nullable=False),
    Column("analysis_id", UUID(as_uuid=True),
           ForeignKey("analysis.analysis.id"),
           primary_key=True,
           nullable=False),
    Column("kvasir_run_id", UUID(as_uuid=True),
           ForeignKey("kvasir_v1.run.id"),
           primary_key=True,
           nullable=False),
    Column("created_at", DateTime(timezone=True),
           nullable=False, default=func.now()),
    schema="kvasir_v1",
)


swe_run = Table(
    "swe_run",
    metadata,
    Column("run_id", UUID(as_uuid=True),
           ForeignKey("kvasir_v1.run.id"),
           primary_key=True,
           nullable=False),
    Column("pipeline_id", UUID(as_uuid=True),
           ForeignKey("pipeline.pipeline.id"),
           nullable=False),
    Column("kvasir_run_id", UUID(as_uuid=True),
           ForeignKey("kvasir_v1.run.id"),
           primary_key=True,
           nullable=False),
    Column("created_at", DateTime(timezone=True),
           nullable=False, default=func.now()),
    schema="kvasir_v1",
)
