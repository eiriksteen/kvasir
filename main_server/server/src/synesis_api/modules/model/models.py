import uuid
from datetime import timezone, datetime
from sqlalchemy import Column, String, ForeignKey, Table, UUID, DateTime, Boolean, CheckConstraint
from sqlalchemy.dialects.postgresql import JSONB
from pgvector.sqlalchemy import Vector

from synesis_api.database.core import metadata
from synesis_api.app_secrets import EMBEDDING_DIM

model_modality_constraint = "modality IN ('time_series', 'tabular', 'multimodal', 'image', 'text', 'audio', 'video')"
model_task_constraint = "task IN ('forecasting', 'classification', 'regression', 'clustering', 'anomaly_detection', 'generation', 'segmentation')"


model = Table(
    "model",
    metadata,
    Column("id", UUID(as_uuid=True),
           default=uuid.uuid4,
           primary_key=True),
    Column("name", String, nullable=False),
    Column("description", String, nullable=False),
    Column("embedding", Vector(dim=EMBEDDING_DIM), nullable=False),
    Column("source_id", UUID(as_uuid=True),
           ForeignKey("model_sources.model_source.id"),
           nullable=False),
    Column("owner_id", UUID(as_uuid=True),
           ForeignKey("auth.users.id"),
           nullable=False),
    Column("public", Boolean, nullable=False),
    Column("modality", String, nullable=False),
    Column("default_config", JSONB, nullable=True),
    Column("programming_language_with_version", String, nullable=False),
    Column("setup_script_path", String, nullable=True),
    Column("task", String, nullable=False),
    Column("inference_function_id", UUID(as_uuid=True),
           ForeignKey("function.function.id"),
           nullable=False),
    Column("training_function_id", UUID(as_uuid=True),
           ForeignKey("function.function.id"),
           nullable=False),
    CheckConstraint(model_modality_constraint),
    CheckConstraint(model_task_constraint),
    Column("created_at", DateTime(timezone=True),
           default=datetime.now(timezone.utc), nullable=False),
    Column("updated_at", DateTime(timezone=True),
           default=datetime.now(timezone.utc),
           onupdate=datetime.now(timezone.utc), nullable=False),
    schema="model"
)


model_entity = Table(
    "model_entity",
    metadata,
    Column("id", UUID(as_uuid=True),
           default=uuid.uuid4,
           primary_key=True),
    Column("model_id", UUID(as_uuid=True),
           ForeignKey("model.model.id"),
           nullable=False),
    # Weights save dir and pipeline id are null for non-trained models
    Column("weights_save_dir", String, nullable=True),
    Column("pipeline_id", UUID(as_uuid=True),
           ForeignKey("pipeline.pipeline.id"),
           nullable=True),
    Column("project_id", UUID(as_uuid=True),
           ForeignKey("project.project.id"),
           nullable=False),
    Column("config", JSONB, nullable=True),
    Column("created_at", DateTime(timezone=True),
           default=datetime.now(timezone.utc), nullable=False),
    Column("updated_at", DateTime(timezone=True),
           default=datetime.now(timezone.utc),
           onupdate=datetime.now(timezone.utc), nullable=False),
    schema="model"
)
