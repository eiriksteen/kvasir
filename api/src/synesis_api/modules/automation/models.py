import uuid
from sqlalchemy import Column, String, ForeignKey, Table, UUID, DateTime, Boolean
from sqlalchemy.dialects.postgresql import JSONB
from synesis_api.database.core import metadata
from datetime import timezone, datetime


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
           ForeignKey("programming_language.id"),
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
           ForeignKey("modality.id"),
           nullable=False),
    Column("source_id", UUID(as_uuid=True),
           ForeignKey("source.id"),
           nullable=False),
    Column("programming_language_version_id", UUID(as_uuid=True),
           ForeignKey("programming_language_version.id"),
           nullable=False),
    Column("setup_script_path", String, nullable=False),
    Column("config_script_path", String, nullable=False),
    Column("input_description", String, nullable=False),
    Column("output_description", String, nullable=False),
    Column("config_parameters", JSONB, nullable=False),
    Column("created_at", DateTime(timezone=True),
           default=datetime.now(timezone.utc), nullable=False),
    schema="automation"
)


model_task = Table(
    "model_task",
    metadata,
    Column("id", UUID(as_uuid=True),
           default=uuid.uuid4,
           primary_key=True),
    Column("model_id", UUID(as_uuid=True),
           ForeignKey("model.id"),
           nullable=False),
    Column("task_id", UUID(as_uuid=True),
           ForeignKey("task.id"),
           nullable=False),
    Column("inference_script_path", String, nullable=False),
    Column("training_script_path", String, nullable=False),
    Column("created_at", DateTime(timezone=True),
           default=datetime.now(timezone.utc), nullable=False),
    schema="automation"
)
