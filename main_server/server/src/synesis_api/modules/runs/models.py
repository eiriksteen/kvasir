import uuid
from sqlalchemy import Table, Column, String, DateTime, func, ForeignKey, CheckConstraint
from sqlalchemy.dialects.postgresql import UUID, BYTEA
from synesis_api.database.core import metadata

# General run models

run = Table(
    "run",
    metadata,
    Column("id", UUID(as_uuid=True), primary_key=True, default=uuid.uuid4),
    # Only for user-facing runs, SWE does not need spec
    Column("user_id", UUID(as_uuid=True),
           ForeignKey("auth.users.id"), nullable=False),
    Column("conversation_id", UUID(as_uuid=True),
           ForeignKey("orchestrator.conversation.id"), nullable=True),
    Column("project_id", UUID(as_uuid=True),
           ForeignKey("project.project.id"), nullable=True),
    Column("parent_run_id", UUID(as_uuid=True),
           ForeignKey("runs.run.id"), nullable=True),
    Column("type", String, nullable=False),
    Column("status", String, nullable=False),
    Column("started_at", DateTime(timezone=True), nullable=False),
    Column("completed_at", DateTime(timezone=True), nullable=True),
    schema="runs"
)


# Run spec is only for user-facing runs
# The run is created with pending status, and the spec is created to display to the user, and allow them to approve or reject it
run_specification = Table(
    "run_specification",
    metadata,
    Column("id", UUID(as_uuid=True), primary_key=True, default=uuid.uuid4),
    Column("run_id", UUID(as_uuid=True),
           ForeignKey("runs.run.id"), nullable=False),
    Column("run_name", String, nullable=False),
    Column("plan_and_deliverable_description_for_user", String, nullable=False),
    Column("plan_and_deliverable_description_for_agent", String, nullable=False),
    Column("questions_for_user", String, nullable=True),
    Column("configuration_defaults_description", String, nullable=True),
    Column("created_at", DateTime(timezone=True),
           nullable=False, default=func.now()),
    Column("updated_at", DateTime(timezone=True),
           nullable=False, default=func.now(), onupdate=func.now()),
    schema="runs"
)


run_message = Table(
    "run_message",
    metadata,
    Column("id", UUID(as_uuid=True), primary_key=True, default=uuid.uuid4),
    Column("content", String, nullable=False),
    Column("run_id", UUID(as_uuid=True),
           ForeignKey("runs.run.id"), nullable=False),
    # tool_call, result, error
    Column("type", String, nullable=True),
    Column("created_at", DateTime(timezone=True),
           nullable=False, default=func.now()),
    schema="runs"
)


run_pydantic_message = Table(
    "run_pydantic_message",
    metadata,
    Column("id", UUID(as_uuid=True), primary_key=True, default=uuid.uuid4),
    Column("run_id", UUID(as_uuid=True),
           ForeignKey("runs.run.id"), nullable=False),
    Column("message_list", BYTEA, nullable=False),
    Column("created_at", DateTime(timezone=True),
           nullable=False, default=func.now()),
    schema="runs"
)


data_source_in_run = Table(
    "data_source_in_run",
    metadata,
    Column("run_id", UUID(as_uuid=True),
           ForeignKey("runs.run.id"), primary_key=True),
    Column("data_source_id", UUID(as_uuid=True),
           ForeignKey("data_sources.data_source.id"), primary_key=True),
    Column("created_at", DateTime(timezone=True),
           nullable=False, default=func.now()),
    schema="runs"
)


dataset_in_run = Table(
    "dataset_in_run",
    metadata,
    Column("run_id", UUID(as_uuid=True),
           ForeignKey("runs.run.id"), primary_key=True),
    Column("dataset_id", UUID(as_uuid=True),
           ForeignKey("data_objects.dataset.id"), primary_key=True),
    Column("created_at", DateTime(timezone=True),
           nullable=False, default=func.now()),
    schema="runs"
)


analysis_in_run = Table(
    "analysis_in_run",
    metadata,
    Column("run_id", UUID(as_uuid=True),
           ForeignKey("runs.run.id"), primary_key=True),
    Column("analysis_id", UUID(as_uuid=True),
           ForeignKey("analysis.analysis_jobs_results.job_id"), primary_key=True),
    Column("created_at", DateTime(timezone=True),
           nullable=False, default=func.now()),
    schema="runs"
)


model_entity_in_run = Table(
    "model_entity_in_run",
    metadata,
    Column("run_id", UUID(as_uuid=True),
           ForeignKey("runs.run.id"), primary_key=True),
    Column("model_entity_id", UUID(as_uuid=True),
           ForeignKey("model.model_entity.id"), primary_key=True),
    Column("created_at", DateTime(timezone=True),
           nullable=False, default=func.now()),
    schema="runs"
)


pipeline_in_run = Table(
    "pipeline_in_run",
    metadata,
    Column("run_id", UUID(as_uuid=True),
           ForeignKey("runs.run.id"), primary_key=True),
    Column("pipeline_id", UUID(as_uuid=True),
           ForeignKey("pipeline.pipeline.id"), primary_key=True),
    Column("created_at", DateTime(timezone=True),
           nullable=False, default=func.now()),
    schema="runs"
)

# Output tables - track entities created by runs

data_source_from_run = Table(
    "data_source_from_run",
    metadata,
    Column("run_id", UUID(as_uuid=True),
           ForeignKey("runs.run.id"), primary_key=True),
    Column("data_source_id", UUID(as_uuid=True),
           ForeignKey("data_sources.data_source.id"), primary_key=True),
    Column("created_at", DateTime(timezone=True),
           nullable=False, default=func.now()),
    schema="runs"
)


dataset_from_run = Table(
    "dataset_from_run",
    metadata,
    Column("run_id", UUID(as_uuid=True),
           ForeignKey("runs.run.id"), primary_key=True),
    Column("dataset_id", UUID(as_uuid=True),
           ForeignKey("data_objects.dataset.id"), primary_key=True),
    Column("created_at", DateTime(timezone=True),
           nullable=False, default=func.now()),
    schema="runs"
)


model_entity_from_run = Table(
    "model_entity_from_run",
    metadata,
    Column("run_id", UUID(as_uuid=True),
           ForeignKey("runs.run.id"), primary_key=True),
    Column("model_entity_id", UUID(as_uuid=True),
           ForeignKey("model.model_entity.id"), primary_key=True),
    Column("created_at", DateTime(timezone=True),
           nullable=False, default=func.now()),
    schema="runs"
)


pipeline_from_run = Table(
    "pipeline_from_run",
    metadata,
    Column("run_id", UUID(as_uuid=True),
           ForeignKey("runs.run.id"), primary_key=True),
    Column("pipeline_id", UUID(as_uuid=True),
           ForeignKey("pipeline.pipeline.id"), primary_key=True),
    Column("created_at", DateTime(timezone=True),
           nullable=False, default=func.now()),
    schema="runs"
)
