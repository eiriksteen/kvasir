import uuid
from datetime import timezone, datetime
from sqlalchemy import Column, String, ForeignKey, Table, UUID, DateTime, Boolean, CheckConstraint, Integer
from sqlalchemy.dialects.postgresql import JSONB
from pgvector.sqlalchemy import Vector

from synesis_api.database.core import metadata
from synesis_api.secrets import EMBEDDING_DIM
from synesis_data_structures.time_series.definitions import get_first_level_structure_ids

# Build the constraint string with proper quotes
structure_ids = get_first_level_structure_ids()
structure_constraint = "structure_id IN (" + \
    ", ".join(f"'{id}'" for id in structure_ids) + ")"


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


function = Table(
    "function",
    metadata,
    Column("id", UUID(as_uuid=True),
           default=uuid.uuid4,
           primary_key=True),
    Column("name", String, nullable=False),
    Column("description", String, nullable=False),
    Column("embedding", Vector(dim=EMBEDDING_DIM), nullable=False),
    Column("implementation_script_path", String, nullable=False),
    Column("setup_script_path", String, nullable=False),
    Column("created_at", DateTime(timezone=True),
           default=datetime.now(timezone.utc), nullable=False),
    Column("updated_at", DateTime(timezone=True),
           default=datetime.now(timezone.utc),
           onupdate=datetime.now(timezone.utc), nullable=False),
    schema="pipeline"
)


function_input = Table(
    "function_input",
    metadata,
    Column("id", UUID(as_uuid=True),
           default=uuid.uuid4,
           primary_key=True),
    Column("function_id", UUID(as_uuid=True),
           ForeignKey("pipeline.function.id"),
           nullable=False),
    Column("structure_id", String, nullable=False),
    Column("name", String, nullable=False),
    Column("description", String, nullable=False),
    Column("required", Boolean, nullable=False),
    CheckConstraint(structure_constraint),
    Column("created_at", DateTime(timezone=True),
           default=datetime.now(timezone.utc), nullable=False),
    Column("updated_at", DateTime(timezone=True),
           default=datetime.now(timezone.utc),
           onupdate=datetime.now(timezone.utc), nullable=False),
    # Ensure the structure id is a valid first level structure id
    CheckConstraint(structure_constraint),
    schema="pipeline"
)


function_output = Table(
    "function_output",
    metadata,
    Column("id", UUID(as_uuid=True),
           default=uuid.uuid4,
           primary_key=True),
    Column("function_id", UUID(as_uuid=True),
           ForeignKey("pipeline.function.id"),
           nullable=False),
    Column("structure_id", String, nullable=False),
    Column("name", String, nullable=False),
    Column("description", String, nullable=False),
    Column("created_at", DateTime(timezone=True),
           default=datetime.now(timezone.utc), nullable=False),
    Column("updated_at", DateTime(timezone=True),
           default=datetime.now(timezone.utc),
           onupdate=datetime.now(timezone.utc), nullable=False),
    # Ensure the structure id is a valid first level structure id
    CheckConstraint(structure_constraint),
    schema="pipeline"
)


function_in_pipeline = Table(
    "function_in_pipeline",
    metadata,
    Column("id", UUID(as_uuid=True),
           default=uuid.uuid4,
           primary_key=True),
    Column("pipeline_id", UUID(as_uuid=True),
           ForeignKey("pipeline.pipeline.id"),
           nullable=False),
    Column("function_id", UUID(as_uuid=True),
           ForeignKey("pipeline.function.id"),
           nullable=False),
    Column("next_function_id", UUID(as_uuid=True),
           ForeignKey("pipeline.function.id"),
           nullable=True),
    Column("created_at", DateTime(timezone=True),
           default=datetime.now(timezone.utc), nullable=False),
    Column("updated_at", DateTime(timezone=True),
           default=datetime.now(timezone.utc),
           onupdate=datetime.now(timezone.utc), nullable=False),
    schema="pipeline"
)


data_object_computed_from_function = Table(
    "data_object_computed_from_function",
    metadata,
    Column("id", UUID(as_uuid=True),
           default=uuid.uuid4,
           primary_key=True),
    Column("data_object_id", UUID(as_uuid=True),
           ForeignKey("data_objects.data_object.id"),
           nullable=False),
    Column("function_id", UUID(as_uuid=True),
           ForeignKey("pipeline.function.id"),
           nullable=False),
    Column("created_at", DateTime(timezone=True),
           default=datetime.now(timezone.utc), nullable=False),
    Column("updated_at", DateTime(timezone=True),
           default=datetime.now(timezone.utc),
           onupdate=datetime.now(timezone.utc), nullable=False),
    schema="pipeline"
)


modality = Table(
    "modality",
    metadata,
    Column("id", UUID(as_uuid=True),
           default=uuid.uuid4,
           primary_key=True),
    Column("name", String, nullable=False),
    Column("description", String, nullable=True),
    Column("created_at", DateTime(timezone=True),
           default=datetime.now(timezone.utc), nullable=False),
    Column("updated_at", DateTime(timezone=True),
           default=datetime.now(timezone.utc),
           onupdate=datetime.now(timezone.utc), nullable=False),
    schema="pipeline"
)


task = Table(
    "task",
    metadata,
    Column("id", UUID(as_uuid=True),
           default=uuid.uuid4,
           primary_key=True),
    Column("name", String, nullable=False),
    Column("description", String, nullable=True),
    Column("created_at", DateTime(timezone=True),
           default=datetime.now(timezone.utc), nullable=False),
    Column("updated_at", DateTime(timezone=True),
           default=datetime.now(timezone.utc),
           onupdate=datetime.now(timezone.utc), nullable=False),
    schema="pipeline"
)


source = Table(
    "source",
    metadata,
    Column("id", UUID(as_uuid=True),
           default=uuid.uuid4,
           primary_key=True),
    Column("name", String, nullable=False),
    Column("description", String, nullable=True),
    Column("created_at", DateTime(timezone=True),
           default=datetime.now(timezone.utc), nullable=False),
    Column("updated_at", DateTime(timezone=True),
           default=datetime.now(timezone.utc),
           onupdate=datetime.now(timezone.utc), nullable=False),
    schema="pipeline"
)


programming_language = Table(
    "programming_language",
    metadata,
    Column("id", UUID(as_uuid=True),
           default=uuid.uuid4,
           primary_key=True),
    Column("name", String, nullable=False),
    Column("description", String, nullable=True),
    Column("created_at", DateTime(timezone=True),
           default=datetime.now(timezone.utc), nullable=False),
    Column("updated_at", DateTime(timezone=True),
           default=datetime.now(timezone.utc),
           onupdate=datetime.now(timezone.utc), nullable=False),
    schema="pipeline"
)


programming_language_version = Table(
    "programming_language_version",
    metadata,
    Column("id", UUID(as_uuid=True),
           default=uuid.uuid4,
           primary_key=True),
    Column("programming_language_id", UUID(as_uuid=True),
           ForeignKey("pipeline.programming_language.id"),
           nullable=False),
    Column("version", String, nullable=False),
    Column("created_at", DateTime(timezone=True),
           default=datetime.now(timezone.utc), nullable=False),
    Column("updated_at", DateTime(timezone=True),
           default=datetime.now(timezone.utc),
           onupdate=datetime.now(timezone.utc), nullable=False),
    schema="pipeline"
)


model = Table(
    "model",
    metadata,
    Column("id", UUID(as_uuid=True),
           default=uuid.uuid4,
           primary_key=True),
    Column("name", String, nullable=False),
    Column("description", String, nullable=False),
    Column("owner_id", UUID(as_uuid=True),
           ForeignKey("auth.users.id"),
           nullable=False),
    Column("public", Boolean, nullable=False, default=False),
    Column("modality_id", UUID(as_uuid=True),
           ForeignKey("pipeline.modality.id"),
           nullable=False),
    Column("source_id", UUID(as_uuid=True),
           ForeignKey("pipeline.source.id"),
           nullable=False),
    Column("programming_language_version_id", UUID(as_uuid=True),
           ForeignKey("pipeline.programming_language_version.id"),
           nullable=False),
    Column("setup_script_path", String, nullable=False),
    Column("config_script_path", String, nullable=False),
    Column("input_description", String, nullable=False),
    Column("output_description", String, nullable=False),
    # TODO: Should have a separate table to define config parameters
    # Very nice to unify the treatment of config parameters for reusability and systemization
    Column("config_parameters", JSONB, nullable=False),
    Column("created_at", DateTime(timezone=True),
           default=datetime.now(timezone.utc), nullable=False),
    Column("updated_at", DateTime(timezone=True),
           default=datetime.now(timezone.utc),
           onupdate=datetime.now(timezone.utc), nullable=False),
    schema="pipeline"
)


# TODO: Add input and output structure defs
model_task = Table(
    "model_task",
    metadata,
    Column("id", UUID(as_uuid=True),
           default=uuid.uuid4,
           primary_key=True),
    Column("model_id", UUID(as_uuid=True),
           ForeignKey("pipeline.model.id"),
           nullable=False),
    Column("task_id", UUID(as_uuid=True),
           ForeignKey("pipeline.task.id"),
           nullable=False),
    Column("inference_script_path", String, nullable=False),
    Column("training_script_path", String, nullable=False),
    Column("inference_function_id", UUID(as_uuid=True),
           ForeignKey("pipeline.function.id"),
           nullable=False),
    Column("training_function_id", UUID(as_uuid=True),
           ForeignKey("pipeline.function.id"),
           nullable=False),
    Column("created_at", DateTime(timezone=True),
           default=datetime.now(timezone.utc), nullable=False),
    Column("updated_at", DateTime(timezone=True),
           default=datetime.now(timezone.utc),
           onupdate=datetime.now(timezone.utc), nullable=False),
    schema="pipeline"
)
