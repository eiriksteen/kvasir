import uuid
from datetime import timezone, datetime
from sqlalchemy import Column, String, ForeignKey, Table, UUID, DateTime, Boolean, CheckConstraint, Integer
from sqlalchemy.dialects.postgresql import JSONB
from pgvector.sqlalchemy import Vector

from synesis_api.database.core import metadata
from synesis_api.app_secrets import EMBEDDING_DIM

from synesis_data_structures.time_series.definitions import get_first_level_structure_ids

structure_ids = get_first_level_structure_ids()

model_modality_constraint = "modality IN ('time_series', 'tabular', 'multimodal', 'image', 'text', 'audio', 'video')"
model_task_constraint = "task IN ('forecasting', 'classification', 'regression', 'clustering', 'anomaly_detection', 'generation', 'segmentation')"
structure_constraint = "structure_id IN (" + \
    ", ".join(f"'{id}'" for id in structure_ids) + ")"
function_type_constraint = "function_type IN ('training', 'inference')"


# Split out definition to enable versioning
model_definition = Table(
    "model_definition",
    metadata,
    Column("id", UUID(as_uuid=True),
           default=uuid.uuid4,
           primary_key=True),
    Column("name", String, nullable=False),
    Column("modality", String, nullable=False),
    Column("task", String, nullable=False),
    Column("public", Boolean, nullable=False),
    Column("created_at", DateTime(timezone=True),
           default=datetime.now(timezone.utc), nullable=False),
    Column("updated_at", DateTime(timezone=True),
           default=datetime.now(timezone.utc),
           onupdate=datetime.now(timezone.utc), nullable=False),
    CheckConstraint(model_modality_constraint),
    CheckConstraint(model_task_constraint),
    schema="model"
)


model = Table(
    "model",
    metadata,
    Column("id", UUID(as_uuid=True),
           default=uuid.uuid4,
           primary_key=True),
    Column("definition_id", UUID(as_uuid=True),
           ForeignKey("model.model_definition.id"),
           nullable=False),
    Column("python_class_name", String, nullable=False),
    Column("version", Integer, nullable=False),
    Column("description", String, nullable=False),
    Column("newest_update_description", String, nullable=False),
    Column("embedding", Vector(dim=EMBEDDING_DIM), nullable=False),
    Column("source_id", UUID(as_uuid=True),
           ForeignKey("model_sources.model_source.id"),
           nullable=False),
    Column("user_id", UUID(as_uuid=True),
           ForeignKey("auth.users.id"),
           nullable=False),
    Column("config_schema", JSONB, nullable=False),
    Column("default_config", JSONB, nullable=False),
    Column("implementation_script_id", UUID(as_uuid=True),
           ForeignKey("code.script.id"),
           nullable=False),
    Column("setup_script_id", UUID(as_uuid=True),
           ForeignKey("code.script.id"),
           nullable=True),
    Column("model_class_docstring", String, nullable=False),
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


model_function_input_object_group_definition = Table(
    "model_function_input_object_group_definition",
    metadata,
    Column("id", UUID(as_uuid=True),
           default=uuid.uuid4,
           primary_key=True),
    Column("function_id", UUID(as_uuid=True),
           ForeignKey("model.model_function.id"),
           nullable=False),
    Column("name", String, nullable=False),
    Column("structure_id", String, nullable=False),
    Column("description", String, nullable=False),
    Column("required", Boolean, nullable=False),
    CheckConstraint(structure_constraint),
    Column("created_at", DateTime(timezone=True),
           default=datetime.now(timezone.utc), nullable=False),
    Column("updated_at", DateTime(timezone=True),
           default=datetime.now(timezone.utc),
           onupdate=datetime.now(timezone.utc), nullable=False),
    schema="model"
)


model_function_output_object_group_definition = Table(
    "model_function_output_object_group_definition",
    metadata,
    Column("id", UUID(as_uuid=True),
           default=uuid.uuid4,
           primary_key=True),
    Column("function_id", UUID(as_uuid=True),
           ForeignKey("model.model_function.id"),
           nullable=False),
    Column("name", String, nullable=True),
    Column("structure_id", String, nullable=False),
    Column("description", String, nullable=False),
    CheckConstraint(structure_constraint),
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
    Column("user_id", UUID(as_uuid=True),
           ForeignKey("auth.users.id"),
           nullable=False),
    Column("name", String, nullable=False),
    Column("description", String, nullable=False),
    Column("config", JSONB, nullable=False),
    # Weights save dir and pipeline id are null for non-trained models
    Column("weights_save_dir", String, nullable=True),
    Column("pipeline_id", UUID(as_uuid=True),
           ForeignKey("pipeline.pipeline.id"),
           nullable=True),
    Column("created_at", DateTime(timezone=True),
           default=datetime.now(timezone.utc), nullable=False),
    Column("updated_at", DateTime(timezone=True),
           default=datetime.now(timezone.utc),
           onupdate=datetime.now(timezone.utc), nullable=False),
    schema="model"
)
