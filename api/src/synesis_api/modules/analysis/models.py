from sqlalchemy import Column, String, ForeignKey, Table, UUID
from synesis_api.database.core import metadata


eda_jobs_results = Table(
    "eda_jobs_results",
    metadata,
    Column("job_id", UUID(as_uuid=True),
           ForeignKey("jobs.jobs.id"),
           primary_key=True),
    Column("basic_eda", String, nullable=True),
    Column("advanced_eda", String, nullable=True),
    Column("independent_eda", String, nullable=True),
    Column("python_code", String, nullable=True),
    Column("ad_hoc", String, nullable=True, default=None),
    Column("dataset_id", UUID(as_uuid=True),
           ForeignKey("integration_jobs_results.dataset_id"),
           nullable=True),
    schema="analysis",
)
