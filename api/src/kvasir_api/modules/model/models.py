import uuid
from datetime import timezone, datetime
from sqlalchemy import Column, String, ForeignKey, Table, UUID, DateTime, Boolean, CheckConstraint
from sqlalchemy.dialects.postgresql import JSONB

from kvasir_api.database.core import metadata

SUPPORTED_MODEL_SOURCES = ["github", "pypi"]

model_modality_constraint = "modality IN ('time_series', 'tabular', 'multimodal', 'image', 'text', 'audio', 'video')"
model_task_constraint = "task IN ('forecasting', 'classification', 'regression', 'clustering', 'anomaly_detection', 'generation', 'segmentation')"
function_type_constraint = "function_type IN ('training', 'inference')"

# Build the constraint string with proper quotes
model_implementation_source_constraint = "source IN (" + \
    ", ".join(f"'{id}'" for id in SUPPORTED_MODEL_SOURCES) + ")"


model = Table(
    "model",
    metadata,
    Column("id", UUID(as_uuid=True),
           default=uuid.uuid4,
           primary_key=True),
    Column("name", String, nullable=False),
    Column("user_id", UUID(as_uuid=True),
           ForeignKey("auth.users.id"),
           nullable=False),
    Column("description", String, nullable=False),
    Column("created_at", DateTime(timezone=True),
           default=datetime.now(timezone.utc), nullable=False),
    Column("updated_at", DateTime(timezone=True),
           default=datetime.now(timezone.utc),
           onupdate=datetime.now(timezone.utc), nullable=False),
    schema="model"
)


model_implementation = Table(
    "model_implementation",
    metadata,
    Column("id", UUID(as_uuid=True),
           ForeignKey("model.model.id"),
           default=uuid.uuid4,
           primary_key=True),
    Column("modality", String, nullable=False),
    Column("task", String, nullable=False),
    Column("public", Boolean, nullable=False),
    Column("python_class_name", String, nullable=False),
    Column("source", String, nullable=False),
    Column("implementation_script_path", String, nullable=False),
    Column("model_class_docstring", String, nullable=False),
    Column("default_config", JSONB, nullable=False),
    Column("config_schema", JSONB, nullable=False),
    Column("training_function_id", UUID(as_uuid=True),
           ForeignKey("model.model_function.id"),
           nullable=False),
    Column("inference_function_id", UUID(as_uuid=True),
           ForeignKey("model.model_function.id"),
           nullable=False),
    Column("created_at", DateTime(timezone=True),
           default=datetime.now(timezone.utc), nullable=False),
    Column("updated_at", DateTime(timezone=True),
           default=datetime.now(timezone.utc),
           onupdate=datetime.now(timezone.utc), nullable=False),
    CheckConstraint(model_modality_constraint),
    CheckConstraint(model_task_constraint),
    CheckConstraint(model_implementation_source_constraint),
    schema="model"
)


model_instantiated = Table(
    "model_instantiated",
    metadata,
    Column("id", UUID(as_uuid=True),
           default=uuid.uuid4,
           primary_key=True),
    Column("model_id", UUID(as_uuid=True),
           ForeignKey("model.model.id"),
           nullable=False),
    Column("name", String, nullable=False),
    Column("user_id", UUID(as_uuid=True),
           ForeignKey("auth.users.id"),
           nullable=False),
    Column("description", String, nullable=False),
    Column("config", JSONB, nullable=False),
    Column("weights_save_dir", String, nullable=True),
    Column("created_at", DateTime(timezone=True),
           default=datetime.now(timezone.utc), nullable=False),
    Column("updated_at", DateTime(timezone=True),
           default=datetime.now(timezone.utc),
           onupdate=datetime.now(timezone.utc), nullable=False),
    schema="model"
)


model_function = Table(
    "model_function",
    metadata,
    Column("id", UUID(as_uuid=True),
           default=uuid.uuid4,
           primary_key=True),
    Column("docstring", String, nullable=False),
    Column("args_schema", JSONB, nullable=False),
    Column("output_variables_schema", JSONB, nullable=False),
    Column("default_args", JSONB, nullable=False),
    Column("created_at", DateTime(timezone=True),
           default=datetime.now(timezone.utc), nullable=False),
    Column("updated_at", DateTime(timezone=True),
           default=datetime.now(timezone.utc),
           onupdate=datetime.now(timezone.utc), nullable=False),
    schema="model"
)
