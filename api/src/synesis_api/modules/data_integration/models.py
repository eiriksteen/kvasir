import uuid
from sqlalchemy import Column, String, ForeignKey, Table, UUID, DateTime, func
from sqlalchemy.dialects.postgresql import BYTEA
from synesis_api.database.core import metadata
from datetime import timezone


integration_jobs_results = Table(
    "integration_jobs_results",
    metadata,
    Column("job_id", UUID(as_uuid=True),
           ForeignKey("jobs.jobs.id"),
           primary_key=True),
    Column("dataset_id", UUID(as_uuid=True), nullable=False),
    Column("python_code", String, nullable=False),
    schema="integration"
)

integration_jobs_local_inputs = Table(
    "integration_jobs_local_inputs",
    metadata,
    Column("job_id", UUID(as_uuid=True),
           ForeignKey("jobs.jobs.id"),
           primary_key=True),
    Column("data_description", String, nullable=False),
    Column("data_directory", String, nullable=False),
    schema="integration"
)

integration_pydantic_message = Table(
    "integration_pydantic_message",
    metadata,
    Column("id", UUID(as_uuid=True),
           default=uuid.uuid4,
           primary_key=True),
    Column("job_id", UUID(as_uuid=True),
           ForeignKey("jobs.jobs.id")),
    Column("message_list", BYTEA, nullable=False),
    Column("created_at", DateTime(timezone=True),
           nullable=False, default=func.now()),
    schema="integration"
)

integration_message = Table(
    "integration_message",
    metadata,
    Column("id", UUID(as_uuid=True),
           default=uuid.uuid4,
           primary_key=True),
    Column("job_id", UUID(as_uuid=True),
           ForeignKey("jobs.jobs.id")),
    Column("content", String, nullable=False),
    Column("type", String, nullable=False),
    Column("role", String, nullable=False),
    Column("created_at", DateTime(timezone=True),
           nullable=False, default=func.now()),
    schema="integration"
)
