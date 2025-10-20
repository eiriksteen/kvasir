import uuid
from datetime import timezone, datetime
from sqlalchemy import Column, String, ForeignKey, Table, UUID, DateTime, CheckConstraint, UniqueConstraint
from sqlalchemy.dialects.postgresql import JSONB
from pgvector.sqlalchemy import Vector

from synesis_api.database.core import metadata
from synesis_data_interface.structures.overview import get_first_level_structure_ids

# Build the constraint string with proper quotes
structure_ids = get_first_level_structure_ids()
structure_constraint = "structure_id IN (" + \
    ", ".join(f"'{id}'" for id in structure_ids) + ")"


# The pipeline entity is the overarching object (where the final pipeline doesn't need to be defined yet)
# To make a pipeline runnable, we "compile" / "index" it from the defined code
# The code is either defined by the agent or by the user
pipeline = Table(
    "pipeline",
    metadata,
    Column("id", UUID(as_uuid=True),
           default=uuid.uuid4,
           primary_key=True),
    Column("user_id", UUID(as_uuid=True),
           ForeignKey("auth.users.id"),
           nullable=False),
    Column("name", String, nullable=False),
    Column("description", String, nullable=True),
    Column("created_at", DateTime(timezone=True),
           default=datetime.now(timezone.utc), nullable=False),
    Column("updated_at", DateTime(timezone=True),
           default=datetime.now(timezone.utc),
           onupdate=datetime.now(timezone.utc), nullable=False),
    schema="pipeline"
)


# "Compiled" pipeline
pipeline_implementation = Table(
    "pipeline_implementation",
    metadata,
    Column("id",
           UUID(as_uuid=True),
           ForeignKey("pipeline.pipeline.id"),
           default=uuid.uuid4,
           primary_key=True),
    Column("python_function_name", String, nullable=False),
    Column("docstring", String, nullable=False),
    Column("description", String, nullable=True),
    Column("args", JSONB, nullable=True),
    Column("args_schema", JSONB, nullable=False),
    Column("output_variables_schema", JSONB, nullable=False),
    Column("implementation_script_id", UUID(as_uuid=True),
           ForeignKey("code.script.id"),
           nullable=False),
    Column("created_at", DateTime(timezone=True),
           default=datetime.now(timezone.utc), nullable=False),
    Column("updated_at", DateTime(timezone=True),
           default=datetime.now(timezone.utc),
           onupdate=datetime.now(timezone.utc), nullable=False),
    schema="pipeline"
)


data_source_in_pipeline = Table(
    "data_source_in_pipeline",
    metadata,
    Column("data_source_id", UUID(as_uuid=True),
           ForeignKey("data_sources.data_source.id"), primary_key=True, nullable=False),
    Column("pipeline_id", UUID(as_uuid=True),
           ForeignKey("pipeline.pipeline.id"), primary_key=True, nullable=False),
    Column("created_at", DateTime(timezone=True),
           default=datetime.now(timezone.utc), nullable=False),
    Column("updated_at", DateTime(timezone=True),
           default=datetime.now(timezone.utc),
           onupdate=datetime.now(timezone.utc), nullable=False),
    schema="pipeline"
)


dataset_in_pipeline = Table(
    "dataset_in_pipeline",
    metadata,
    Column("dataset_id", UUID(as_uuid=True),
           ForeignKey("data_objects.dataset.id"), primary_key=True, nullable=False),
    Column("pipeline_id", UUID(as_uuid=True),
           ForeignKey("pipeline.pipeline.id"), primary_key=True, nullable=False),
    Column("created_at", DateTime(timezone=True),
           default=datetime.now(timezone.utc), nullable=False),
    Column("updated_at", DateTime(timezone=True),
           default=datetime.now(timezone.utc),
           onupdate=datetime.now(timezone.utc), nullable=False),
    schema="pipeline"
)


model_entity_in_pipeline = Table(
    "model_entity_in_pipeline",
    metadata,
    Column("model_entity_id", UUID(as_uuid=True),
           ForeignKey("model.model_entity.id"), primary_key=True, nullable=False),
    Column("pipeline_id", UUID(as_uuid=True),
           ForeignKey("pipeline.pipeline.id"), primary_key=True, nullable=False),
    Column("created_at", DateTime(timezone=True),
           default=datetime.now(timezone.utc), nullable=False),
    Column("updated_at", DateTime(timezone=True),
           default=datetime.now(timezone.utc),
           onupdate=datetime.now(timezone.utc), nullable=False),
    schema="pipeline"
)


function_in_pipeline = Table(
    "function_in_pipeline",
    metadata,
    Column("pipeline_id", UUID(as_uuid=True),
           ForeignKey("pipeline.pipeline.id"),
           primary_key=True,
           nullable=False),
    Column("function_id", UUID(as_uuid=True),
           ForeignKey("function.function.id"),
           primary_key=True,
           nullable=False),
    Column("created_at", DateTime(timezone=True),
           default=datetime.now(timezone.utc), nullable=False),
    Column("updated_at", DateTime(timezone=True),
           default=datetime.now(timezone.utc),
           onupdate=datetime.now(timezone.utc), nullable=False),
    schema="pipeline"
)


pipeline_run = Table(
    "pipeline_run",
    metadata,
    Column("id", UUID(as_uuid=True),
           default=uuid.uuid4,
           primary_key=True),
    Column("pipeline_id", UUID(as_uuid=True),
           ForeignKey("pipeline.pipeline.id"),
           nullable=False),
    Column("status", String, nullable=False),
    Column("start_time", DateTime(timezone=True), nullable=False),
    Column("end_time", DateTime(timezone=True), nullable=True),
    Column("created_at", DateTime(timezone=True),
           default=datetime.now(timezone.utc), nullable=False),
    Column("updated_at", DateTime(timezone=True),
           default=datetime.now(timezone.utc),
           onupdate=datetime.now(timezone.utc), nullable=False),
    schema="pipeline"
)


pipeline_output_dataset = Table(
    "pipeline_output_dataset",
    metadata,
    Column("pipeline_id", UUID(as_uuid=True),
           ForeignKey("pipeline.pipeline.id"), primary_key=True, nullable=False),
    Column("dataset_id", UUID(as_uuid=True),
           ForeignKey("data_objects.dataset.id"), primary_key=True, nullable=False),
    Column("created_at", DateTime(timezone=True),
           default=datetime.now(timezone.utc), nullable=False),
    Column("updated_at", DateTime(timezone=True),
           default=datetime.now(timezone.utc),
           onupdate=datetime.now(timezone.utc), nullable=False),
    schema="pipeline"
)


pipeline_output_model_entity = Table(
    "pipeline_output_model_entity",
    metadata,
    Column("pipeline_id", UUID(as_uuid=True),
           ForeignKey("pipeline.pipeline.id"), primary_key=True, nullable=False),
    Column("model_entity_id", UUID(as_uuid=True),
           ForeignKey("model.model_entity.id"), primary_key=True, nullable=False),
    Column("created_at", DateTime(timezone=True),
           default=datetime.now(timezone.utc), nullable=False),
    Column("updated_at", DateTime(timezone=True),
           default=datetime.now(timezone.utc),
           onupdate=datetime.now(timezone.utc), nullable=False),
    schema="pipeline"
)
