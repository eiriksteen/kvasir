import uuid
from sqlalchemy import Column, String, DateTime, ForeignKey, Table, UUID
from ...database.core import metadata

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
    Column("api_key_id",
           UUID(as_uuid=True),
           ForeignKey("auth.user_api_keys.id"),
           nullable=False),
    Column("started_at", DateTime, nullable=False),
    Column("completed_at", DateTime, nullable=True),
    schema="jobs"
)
