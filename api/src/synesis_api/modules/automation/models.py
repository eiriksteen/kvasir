import uuid
from sqlalchemy import Column, String, ForeignKey, Table, UUID
from ...database.core import metadata


model_job_result = Table(
    "model_job_result",
    metadata,
    Column("id", UUID(as_uuid=True), primary_key=True, default=uuid.uuid4),
    Column("job_id", UUID(as_uuid=True),
           ForeignKey("shared.jobs.id"), nullable=False),
    Column("explanation", String, nullable=False),
    Column("python_code", String, nullable=False),
    schema="automation"
)


automation = Table(
    "automation",
    metadata,
    Column("id", UUID(as_uuid=True), primary_key=True, default=uuid.uuid4),
    Column("name", String, nullable=False),
    schema="automation"
)
