import uuid
from sqlalchemy import Table, Column, String, DateTime, func, ForeignKey, CheckConstraint
from sqlalchemy.dialects.postgresql import UUID, BYTEA
from synesis_api.database.core import metadata

# General run models

run = Table(
    "run",
    metadata,
    Column("id", UUID(as_uuid=True), primary_key=True, default=uuid.uuid4),
    Column("user_id", UUID(as_uuid=True),
           ForeignKey("auth.users.id"), nullable=False),
    Column("conversation_id", UUID(as_uuid=True),
           ForeignKey("orchestrator.conversation.id"), nullable=True),
    Column("parent_run_id", UUID(as_uuid=True),
           ForeignKey("runs.run.id"), nullable=True),
    Column("type", String, nullable=False),
    Column("status", String, nullable=False),
    Column("started_at", DateTime(timezone=True), nullable=False),
    Column("completed_at", DateTime(timezone=True), nullable=True),
    Column("run_name", String, nullable=True),
    CheckConstraint(
        "type IN ('data_integration', 'analysis', 'pipeline', 'swe', 'data_source_analysis', 'model_integration')", name="type_check"),
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


# Run-type specific models

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

data_integration_run_input = Table(
    "data_integration_run_input",
    metadata,
    Column("run_id",
           UUID(as_uuid=True),
           ForeignKey("runs.run.id"),
           primary_key=True),
    Column("target_dataset_description", String, nullable=False),
    Column("created_at", DateTime(timezone=True),
           nullable=False, default=func.now()),
    Column("updated_at", DateTime(timezone=True),
           nullable=False, default=func.now(), onupdate=func.now()),
    schema="runs"
)


# model_integration_run_input = Table(
#     "model_integration_run_input",
#     metadata,
#     Column("run_id", UUID(as_uuid=True),
#            ForeignKey("runs.run.id"),
#            primary_key=True),
#     Column("model_id_str", String, nullable=False),
#     Column("source", String, nullable=False),
#     Column("created_at", DateTime(timezone=True),
#            nullable=False, default=func.now()),
#     Column("updated_at", DateTime(timezone=True),
#            nullable=False, default=func.now(), onupdate=func.now()),
#     schema="runs"
# )


data_integration_run_result = Table(
    "data_integration_run_result",
    metadata,
    Column("run_id",
           UUID(as_uuid=True),
           ForeignKey("runs.run.id"),
           primary_key=True),
    Column("dataset_id", UUID(as_uuid=True), ForeignKey(
        "data_objects.dataset.id"), nullable=False),
    Column("code_explanation", String, nullable=False),
    Column("python_code_path", String, nullable=False),
    Column("created_at", DateTime(timezone=True),
           nullable=False, default=func.now()),
    Column("updated_at", DateTime(timezone=True),
           nullable=False, default=func.now(), onupdate=func.now()),
    schema="runs"
)


# model_integration_run_result = Table(
#     "model_integration_run_result",
#     metadata,
#     Column("run_id", UUID(as_uuid=True),
#            ForeignKey("runs.run.id"),
#            primary_key=True),
#     Column("model_id", UUID(as_uuid=True), ForeignKey(
#         "pipeline.model.id"), nullable=False),
#     Column("created_at", DateTime(timezone=True),
#            nullable=False, default=func.now()),
#     Column("updated_at", DateTime(timezone=True),
#            nullable=False, default=func.now(), onupdate=func.now()),
#     schema="runs"
# )
