from sqlalchemy import Column, String, ForeignKey, Table, UUID
from synesis_api.database.core import metadata
from sqlalchemy import Column, String, ForeignKey, Table, UUID, DateTime, Boolean, Integer
from synesis_api.database.core import metadata
from sqlalchemy.dialects.postgresql import JSONB
import uuid

analysis_jobs_results = Table(
    "analysis_jobs_results",
    metadata,
    Column("job_id", UUID(as_uuid=True),
           ForeignKey("jobs.job.id"),
           primary_key=True),
    Column("name", String, nullable=False),
    Column("number_of_datasets", Integer, nullable=False),
    Column("number_of_automations", Integer, nullable=False),
    Column("analysis_plan", JSONB, nullable=False),
    Column("created_at", DateTime(timezone=True), nullable=False),
    Column("pdf_created", Boolean, nullable=False),
    Column("pdf_s3_path", String, nullable=True),
    Column("user_id", UUID(as_uuid=True), ForeignKey(
        "auth.users.id"), nullable=False),
    schema="analysis",
)

analysis_jobs_datasets = Table(
    "analysis_jobs_datasets",
    metadata,
    Column("id", UUID(as_uuid=True),
           primary_key=True,
           default=uuid.uuid4),
    Column("job_id", UUID(as_uuid=True),
           ForeignKey("jobs.job.id"),
           nullable=False),
    Column("dataset_id", UUID(as_uuid=True),
           ForeignKey("data_objects.dataset.id"),
           nullable=False),
    schema="analysis",
)

analysis_jobs_automations = Table(
    "analysis_jobs_automations",
    metadata,
    Column("id", UUID(as_uuid=True),
           primary_key=True,
           default=uuid.uuid4),
    Column("job_id", UUID(as_uuid=True),
           ForeignKey("jobs.job.id"),
           nullable=False),
    Column("automation_id", UUID(as_uuid=True),
           ForeignKey("automation.automation.id"),
           nullable=False),
    schema="analysis",
)

analysis_status_messages = Table(
    "analysis_status_messages",
    metadata,
    Column("id", UUID(as_uuid=True),
           primary_key=True,
           default=uuid.uuid4),
    Column("job_id", UUID(as_uuid=True),
           ForeignKey("jobs.job.id"),
           nullable=False),
    Column("type", String, nullable=False),
    Column("message", String, nullable=False),
    Column("created_at", DateTime(timezone=True), nullable=False),
    schema="analysis",
)
