from sqlalchemy import Column, String, ForeignKey, Table, UUID
from ..database.core import metadata


eda_jobs_results = Table(
    "eda_jobs_results",
    metadata,
    Column("job_id", UUID(as_uuid=True),
           ForeignKey("eda_jobs.id"),
           primary_key=True),
    Column("detailed_summary", String, nullable=False),
    Column("python_code", String, nullable=False),
)
