import uuid
from sqlalchemy import Column, String, ForeignKey, Table, UUID, DateTime, Boolean, Integer
from sqlalchemy.dialects.postgresql import JSONB

from synesis_api.database.core import metadata

analysis_jobs_results = Table(
    "analysis_jobs_results",
    metadata,
    Column("job_id", UUID(as_uuid=True),
           ForeignKey("runs.run.id"),
           primary_key=True),
    Column("name", String, nullable=False),
    Column("number_of_datasets", Integer, nullable=False),
    Column("number_of_pipelines", Integer, nullable=False),
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
           ForeignKey("runs.run.id"),
           nullable=False),
    Column("dataset_id", UUID(as_uuid=True),
           ForeignKey("data_objects.dataset.id"),
           nullable=False),
    schema="analysis",
)

analysis_jobs_pipelines = Table(
    "analysis_jobs_pipelines",
    metadata,
    Column("id", UUID(as_uuid=True),
           primary_key=True,
           default=uuid.uuid4),
    Column("job_id", UUID(as_uuid=True),
           ForeignKey("runs.run.id"),
           nullable=False),
    Column("pipeline_id", UUID(as_uuid=True),
           ForeignKey("pipeline.pipeline.id"),
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
           ForeignKey("runs.run.id"),
           nullable=False),
    Column("type", String, nullable=False),
    Column("message", String, nullable=False),
    Column("created_at", DateTime(timezone=True), nullable=False),
    schema="analysis",
)
