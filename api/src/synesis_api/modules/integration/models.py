from sqlalchemy import Column, String, ForeignKey, Table, UUID
from ...database.core import metadata


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
