import uuid
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy import Table, Column, String, DateTime, func, ForeignKey, PrimaryKeyConstraint, Float

from synesis_api.database.core import metadata


project = Table(
    "project",
    metadata,
    Column("id", UUID(as_uuid=True), primary_key=True, default=uuid.uuid4),
    Column("user_id", UUID(as_uuid=True), ForeignKey(
        "auth.users.id"), nullable=False),
    Column("name", String, nullable=False),
    Column("python_package_name", String, nullable=False),
    Column("description", String, nullable=False),
    Column("view_port_x", Float, nullable=False, default=0.0),
    Column("view_port_y", Float, nullable=False, default=0.0),
    Column("view_port_zoom", Float, nullable=False, default=1.0),
    Column("created_at", DateTime(timezone=True),
           nullable=False, default=func.now()),
    Column("updated_at", DateTime(timezone=True), nullable=False,
           default=func.now(), onupdate=func.now()),
    schema="project"
)


project_data_source = Table(
    "project_data_source",
    metadata,
    Column("project_id", UUID(as_uuid=True), ForeignKey(
        "project.project.id"), nullable=False),
    Column("data_source_id", UUID(as_uuid=True), ForeignKey(
        "data_sources.data_source.id"), nullable=False),
    Column("x_position", Float, nullable=False),
    Column("y_position", Float, nullable=False),
    Column("created_at", DateTime(timezone=True),
           nullable=False, default=func.now()),
    Column("updated_at", DateTime(timezone=True), nullable=False,
           default=func.now(), onupdate=func.now()),
    PrimaryKeyConstraint("project_id", "data_source_id"),
    schema="project"
)


project_dataset = Table(
    "project_dataset",
    metadata,
    Column("project_id", UUID(as_uuid=True), ForeignKey(
        "project.project.id"), nullable=False),
    Column("dataset_id", UUID(as_uuid=True), ForeignKey(
        "data_objects.dataset.id"), nullable=False),
    Column("x_position", Float, nullable=False),
    Column("y_position", Float, nullable=False),
    Column("created_at", DateTime(timezone=True),
           nullable=False, default=func.now()),
    Column("updated_at", DateTime(timezone=True), nullable=False,
           default=func.now(), onupdate=func.now()),
    PrimaryKeyConstraint("project_id", "dataset_id"),
    schema="project"
)


project_analysis = Table(
    "project_analysis",
    metadata,
    Column("project_id", UUID(as_uuid=True), ForeignKey(
        "project.project.id"), nullable=False),
    Column("analysis_id", UUID(as_uuid=True), ForeignKey(
        "analysis.analysis.id"), nullable=False),
    Column("x_position", Float, nullable=False),
    Column("y_position", Float, nullable=False),
    Column("created_at", DateTime(timezone=True),
           nullable=False, default=func.now()),
    Column("updated_at", DateTime(timezone=True), nullable=False,
           default=func.now(), onupdate=func.now()),
    PrimaryKeyConstraint("project_id", "analysis_id"),
    schema="project"
)


project_pipeline = Table(
    "project_pipeline",
    metadata,
    Column("project_id", UUID(as_uuid=True), ForeignKey(
        "project.project.id"), nullable=False),
    Column("pipeline_id", UUID(as_uuid=True), ForeignKey(
        "pipeline.pipeline.id"), nullable=False),
    Column("x_position", Float, nullable=False),
    Column("y_position", Float, nullable=False),
    Column("created_at", DateTime(timezone=True),
           nullable=False, default=func.now()),
    Column("updated_at", DateTime(timezone=True), nullable=False,
           default=func.now(), onupdate=func.now()),
    PrimaryKeyConstraint("project_id", "pipeline_id"),
    schema="project"
)


project_model_entity = Table(
    "project_model_entity",
    metadata,
    Column("project_id", UUID(as_uuid=True), ForeignKey(
        "project.project.id"), nullable=False),
    Column("model_entity_id", UUID(as_uuid=True), ForeignKey(
        "model.model_entity.id"), nullable=False),
    Column("x_position", Float, nullable=False),
    Column("y_position", Float, nullable=False),
    Column("created_at", DateTime(timezone=True),
           nullable=False, default=func.now()),
    Column("updated_at", DateTime(timezone=True), nullable=False,
           default=func.now(), onupdate=func.now()),
    PrimaryKeyConstraint("project_id", "model_entity_id"),
    schema="project"
)
