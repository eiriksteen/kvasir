import uuid
from sqlalchemy import Column, ForeignKey, Table, UUID, DateTime, func, String
from sqlalchemy.dialects.postgresql import BYTEA
from synesis_api.database.core import metadata


model_integration_job_input = Table(
    "model_integration_job_input",
    metadata,
    Column("job_id", UUID(as_uuid=True),
           ForeignKey("jobs.job.id"),
           primary_key=True),
    Column("model_id_str", String, nullable=False),
    Column("source", String, nullable=False),
    Column("created_at", DateTime(timezone=True),
           nullable=False, default=func.now()),
    Column("updated_at", DateTime(timezone=True),
           nullable=False, default=func.now(), onupdate=func.now()),
    schema="model_integration"
)


model_integration_job_result = Table(
    "model_integration_job_result",
    metadata,
    Column("job_id", UUID(as_uuid=True),
           ForeignKey("jobs.job.id"),
           primary_key=True),
    Column("model_id", UUID(as_uuid=True), nullable=False),
    Column("created_at", DateTime(timezone=True),
           nullable=False, default=func.now()),
    Column("updated_at", DateTime(timezone=True),
           nullable=False, default=func.now(), onupdate=func.now()),
    schema="model_integration"
)
