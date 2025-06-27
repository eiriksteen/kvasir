import uuid
from sqlalchemy import Column, String, ForeignKey, Table, UUID, DateTime, func
from sqlalchemy.dialects.postgresql import BYTEA
from synesis_api.database.core import metadata


model_integration_jobs_results = Table(
    "integration_jobs_results",
    metadata,
    Column("job_id", UUID(as_uuid=True),
           ForeignKey("jobs.jobs.id"),
           primary_key=True),
    Column("model_id", UUID(as_uuid=True), nullable=False),
    schema="model_integration"
)

model_integration_pydantic_message = Table(
    "model_integration_pydantic_message",
    metadata,
    Column("id", UUID(as_uuid=True),
           default=uuid.uuid4,
           primary_key=True),
    Column("job_id", UUID(as_uuid=True),
           ForeignKey("jobs.jobs.id")),
    Column("message_list", BYTEA, nullable=False),
    Column("created_at", DateTime(timezone=True),
           nullable=False, default=func.now()),
    schema="model_integration"
)

model_integration_message = Table(
    "model_integration_message",
    metadata,
    Column("id", UUID(as_uuid=True),
           default=uuid.uuid4,
           primary_key=True),
    Column("job_id", UUID(as_uuid=True),
           ForeignKey("jobs.jobs.id")),
    Column("content", String, nullable=False),
    Column("stage", String, nullable=False),
    Column("current_task", String, nullable=True),
    Column("type", String, nullable=False),
    Column("created_at", DateTime(timezone=True),
           nullable=False, default=func.now()),
    schema="model_integration"
)
