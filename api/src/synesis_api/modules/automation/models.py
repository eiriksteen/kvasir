import uuid
from datetime import timezone, datetime
from sqlalchemy import Column, String, ForeignKey, Table, UUID, DateTime, Boolean, CheckConstraint
from sqlalchemy.dialects.postgresql import JSONB
from synesis_api.database.core import metadata
from synesis_data_structures.time_series.definitions import get_first_level_structure_ids


automation = Table(
    "automation",
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
    schema="automation"
)


function = Table(
    "function",
    metadata,
    Column("id", UUID(as_uuid=True),
           default=uuid.uuid4,
           primary_key=True),
    Column("name", String, nullable=False),
    Column("description", String, nullable=True),
    Column("script_path", String, nullable=False),
    Column("created_at", DateTime(timezone=True),
           default=datetime.now(timezone.utc), nullable=False),
    Column("updated_at", DateTime(timezone=True),
           default=datetime.now(timezone.utc),
           onupdate=datetime.now(timezone.utc), nullable=False),
    schema="automation"
)


function_input_structure = Table(
    "function_input_structure",
    metadata,
    Column("id", UUID(as_uuid=True),
           default=uuid.uuid4,
           primary_key=True),
    Column("function_id", UUID(as_uuid=True),
           ForeignKey("automation.function.id"),
           nullable=False),
    Column("structure_id", String, nullable=False),
    Column("name", String, nullable=False),
    Column("description", String, nullable=True),
    Column("type", String, nullable=False),
    Column("required", Boolean, nullable=False),
    CheckConstraint(
        f"structure_id IN ({', '.join(get_first_level_structure_ids())})"),
    Column("created_at", DateTime(timezone=True),
           default=datetime.now(timezone.utc), nullable=False),
    Column("updated_at", DateTime(timezone=True),
           default=datetime.now(timezone.utc),
           onupdate=datetime.now(timezone.utc), nullable=False),
    schema="automation"
)


function_output_structure = Table(
    "function_output_structure",
    metadata,
    Column("id", UUID(as_uuid=True),
           default=uuid.uuid4,
           primary_key=True),
    Column("function_id", UUID(as_uuid=True),
           ForeignKey("automation.function.id"),
           nullable=False),
    Column("structure_id", String, nullable=False),
    Column("name", String, nullable=False),
    Column("description", String, nullable=True),
    Column("type", String, nullable=False),
    CheckConstraint(
        f"structure_id IN ({', '.join(get_first_level_structure_ids())})"),
    Column("created_at", DateTime(timezone=True),
           default=datetime.now(timezone.utc), nullable=False),
    Column("updated_at", DateTime(timezone=True),
           default=datetime.now(timezone.utc),
           onupdate=datetime.now(timezone.utc), nullable=False),
    schema="automation"
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
           ForeignKey("automation.function.id"),
           nullable=False),
    Column("created_at", DateTime(timezone=True),
           default=datetime.now(timezone.utc), nullable=False),
    Column("updated_at", DateTime(timezone=True),
           default=datetime.now(timezone.utc),
           onupdate=datetime.now(timezone.utc), nullable=False),
    schema="automation"
)


modality = Table(
    "modality",
    metadata,
    Column("id", UUID(as_uuid=True),
           default=uuid.uuid4,
           primary_key=True),
    Column("name", String, nullable=False),
    Column("description", String, nullable=True),
    schema="automation"
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
    schema="automation"
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
    schema="automation"
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
    schema="automation"
)


programming_language_version = Table(
    "programming_language_version",
    metadata,
    Column("id", UUID(as_uuid=True),
           default=uuid.uuid4,
           primary_key=True),
    Column("programming_language_id", UUID(as_uuid=True),
           ForeignKey("automation.programming_language.id"),
           nullable=False),
    Column("version", String, nullable=False),
    Column("created_at", DateTime(timezone=True),
           default=datetime.now(timezone.utc), nullable=False),
    schema="automation"
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
           ForeignKey("automation.modality.id"),
           nullable=False),
    Column("source_id", UUID(as_uuid=True),
           ForeignKey("automation.source.id"),
           nullable=False),
    Column("programming_language_version_id", UUID(as_uuid=True),
           ForeignKey("automation.programming_language_version.id"),
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
    schema="automation"
)


# TODO: Add input and output structure defs
model_task = Table(
    "model_task",
    metadata,
    Column("id", UUID(as_uuid=True),
           default=uuid.uuid4,
           primary_key=True),
    Column("model_id", UUID(as_uuid=True),
           ForeignKey("automation.model.id"),
           nullable=False),
    Column("task_id", UUID(as_uuid=True),
           ForeignKey("automation.task.id"),
           nullable=False),
    Column("inference_script_path", String, nullable=False),
    Column("training_script_path", String, nullable=False),
    Column("inference_function_id", UUID(as_uuid=True),
           ForeignKey("automation.function.id"),
           nullable=False),
    Column("training_function_id", UUID(as_uuid=True),
           ForeignKey("automation.function.id"),
           nullable=False),
    Column("created_at", DateTime(timezone=True),
           default=datetime.now(timezone.utc), nullable=False),
    schema="automation"
)
