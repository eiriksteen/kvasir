import uuid
from sqlalchemy import Table, Column, String, DateTime, func, ForeignKey, PrimaryKeyConstraint
from sqlalchemy.dialects.postgresql import UUID, BYTEA, JSONB
from synesis_api.database.core import metadata


# Models specific to Kvasir V1 Agent

results_queue = Table(
    "results_queue",
    metadata,
    Column("id", UUID(as_uuid=True), primary_key=True, default=uuid.uuid4),
    Column("run_id", UUID(as_uuid=True),
           ForeignKey("runs.run.id"), nullable=False),
    Column("content", JSONB, nullable=False),
    Column("created_at", DateTime(timezone=True),
           nullable=False, default=func.now()),
    schema="kvasir_v1"
)


deps = Table(
    "swe_deps",
    metadata,
    Column("id", UUID(as_uuid=True), primary_key=True, default=uuid.uuid4),
    Column("run_id", UUID(as_uuid=True),
           ForeignKey("runs.run.id"), nullable=False),
    # swe, analysis, orchestrator
    Column("type", String, nullable=False),
    Column("content", String, nullable=False),
    Column("created_at", DateTime(timezone=True),
           nullable=False, default=func.now()),
    schema="kvasir_v1"
)


result = Table(
    "result",
    metadata,
    Column("id", UUID(as_uuid=True), primary_key=True, default=uuid.uuid4),
    Column("run_id", UUID(as_uuid=True),
           ForeignKey("runs.run.id"), nullable=False),
    # swe, analysis
    Column("type", String, nullable=False),
    Column("content", String, nullable=False),
    Column("created_at", DateTime(timezone=True),
           nullable=False, default=func.now()),
    schema="kvasir_v1"
)


pydantic_ai_message = Table(
    "pydantic_ai_message",
    metadata,
    Column("id", UUID(as_uuid=True), primary_key=True, default=uuid.uuid4),
    Column("run_id", UUID(as_uuid=True),
           ForeignKey("runs.run.id"), nullable=False),
    Column("message_list", BYTEA, nullable=False),
    Column("created_at", DateTime(timezone=True),
           nullable=False, default=func.now()),
    schema="kvasir_v1"
)
