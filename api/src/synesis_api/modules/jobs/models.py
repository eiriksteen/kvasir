import uuid
from sqlalchemy import Column, String, DateTime, ForeignKey, Table, UUID
from synesis_api.database.core import metadata
from datetime import timezone

# Integration Job Metadata table
jobs = Table(
    "jobs",
    metadata,
    Column("id", UUID(as_uuid=True), primary_key=True, default=uuid.uuid4),
    Column("type", String, nullable=False),
    Column("status", String, nullable=False),
    Column("user_id",
           UUID(as_uuid=True),
           ForeignKey("auth.users.id"),
           nullable=False),
    Column("started_at", DateTime(timezone=True), nullable=False),
    Column("completed_at", DateTime(timezone=True), nullable=True),
    Column("job_name", String, nullable=True),
    schema="jobs"
)
