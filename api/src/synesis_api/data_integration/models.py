import uuid
from sqlalchemy import Column, String, DateTime, ForeignKey, Table, UUID
from sqlalchemy.dialects.postgresql import ARRAY
from ..database.core import metadata

# Integration Job Metadata table
integration_jobs = Table(
    "integration_jobs",
    metadata,
    Column("id", UUID(as_uuid=True), primary_key=True, default=uuid.uuid4),
    Column("status", String, nullable=False),
    Column("user_id", UUID(as_uuid=True),
           ForeignKey("users.id"), nullable=False),
    Column("api_key_id", UUID(as_uuid=True),
           ForeignKey("user_api_keys.id"), nullable=False),
    Column("started_at", DateTime, nullable=False),
    Column("completed_at", DateTime, nullable=True),
)


integration_jobs_results = Table(
    "integration_jobs_results",
    metadata,
    Column("job_id", UUID(as_uuid=True),
           ForeignKey("integration_jobs.id"),
           primary_key=True),
    Column("dataset_id", UUID(as_uuid=True), nullable=False),
    Column("python_code", String, nullable=False)
)
