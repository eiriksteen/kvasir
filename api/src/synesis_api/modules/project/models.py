import uuid
from sqlalchemy import Table, Column, String, DateTime, func, ForeignKey, PrimaryKeyConstraint
from sqlalchemy.dialects.postgresql import UUID
from synesis_api.database.core import metadata


project = Table(
    "project",
    metadata,
    Column("id", UUID(as_uuid=True), primary_key=True, default=uuid.uuid4),
    Column("user_id", UUID(as_uuid=True), ForeignKey(
        "auth.users.id"), nullable=False),
    Column("name", String, nullable=False),
    Column("description", String, nullable=False),
    Column("created_at", DateTime(timezone=True),
           nullable=False, default=func.now()),
    Column("updated_at", DateTime(timezone=True), nullable=False,
           default=func.now(), onupdate=func.now()),
    schema="project"
)


project_dataset = Table(
    "project_dataset",
    metadata,
    Column("project_id", UUID(as_uuid=True), ForeignKey(
        "project.project.id"), nullable=False),
    Column("dataset_id", UUID(as_uuid=True), ForeignKey(
        "data_objects.dataset.id"), nullable=False),
    PrimaryKeyConstraint("project_id", "dataset_id"),
    schema="project"
)


project_analysis = Table(
    "project_analysis",
    metadata,
    Column("project_id", UUID(as_uuid=True), ForeignKey(
        "project.project.id"), nullable=False),
    Column("analysis_id", UUID(as_uuid=True), ForeignKey(
        "analysis.analysis_jobs_results.job_id"), nullable=False),
    PrimaryKeyConstraint("project_id", "analysis_id"),
    schema="project"
)


project_automation = Table(
    "project_automation",
    metadata,
    Column("project_id", UUID(as_uuid=True), ForeignKey(
        "project.project.id"), nullable=False),
    Column("automation_id", UUID(as_uuid=True), nullable=False),
    PrimaryKeyConstraint("project_id", "automation_id"),
    schema="project"
)
