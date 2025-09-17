import uuid
from datetime import timezone, datetime
from sqlalchemy import Column, String, ForeignKey, Table, UUID, DateTime, Boolean, CheckConstraint, Integer, Float
from sqlalchemy.dialects.postgresql import JSONB
from pgvector.sqlalchemy import Vector

from synesis_api.database.core import metadata
from synesis_api.app_secrets import EMBEDDING_DIM
from synesis_data_structures.time_series.definitions import get_first_level_structure_ids

# Build the constraint string with proper quotes
structure_ids = get_first_level_structure_ids()
structure_constraint = "structure_id IN (" + \
    ", ".join(f"'{id}'" for id in structure_ids) + ")"


function_type_constraint = "type IN ('inference', 'training', 'computation')"


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


pipeline_periodic_schedule = Table(
    "pipeline_periodic_schedule",
    metadata,
    Column("id", UUID(as_uuid=True),
           default=uuid.uuid4,
           primary_key=True),
    Column("pipeline_id", UUID(as_uuid=True),
           ForeignKey("pipeline.pipeline.id"),
           nullable=False),
    Column("start_time", DateTime(timezone=True), nullable=False),
    Column("end_time", DateTime(timezone=True), nullable=True),
    Column("schedule_description", String, nullable=True),
    Column("cron_expression", String, nullable=True),
    Column("created_at", DateTime(timezone=True),
           default=datetime.now(timezone.utc), nullable=False),
    Column("updated_at", DateTime(timezone=True),
           default=datetime.now(timezone.utc),
           onupdate=datetime.now(timezone.utc), nullable=False),
    schema="pipeline"
)


pipeline_on_event_schedule = Table(
    "pipeline_on_event_schedule",
    metadata,
    Column("id", UUID(as_uuid=True),
           default=uuid.uuid4,
           primary_key=True),
    Column("pipeline_id", UUID(as_uuid=True),
           ForeignKey("pipeline.pipeline.id"),
           nullable=False),
    Column("event_listener_script_path", String, nullable=False),
    Column("event_description", String, nullable=False),
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


pipeline_inference_run_object_group_result = Table(
    "pipeline_inference_run_object_group_result",
    metadata,
    Column("id", UUID(as_uuid=True),
           default=uuid.uuid4,
           primary_key=True),
    Column("pipeline_run_id", UUID(as_uuid=True),
           ForeignKey("pipeline.pipeline_run.id"),
           nullable=False),
    Column("object_group_id", UUID(as_uuid=True),
           ForeignKey("data_objects.object_group.id"),
           nullable=False),
    Column("created_at", DateTime(timezone=True),
           default=datetime.now(timezone.utc), nullable=False),
    Column("updated_at", DateTime(timezone=True),
           default=datetime.now(timezone.utc),
           onupdate=datetime.now(timezone.utc), nullable=False),
    schema="pipeline"
)


pipeline_run_variables_result = Table(
    "pipeline_run_variables_result",
    metadata,
    Column("id", UUID(as_uuid=True),
           default=uuid.uuid4,
           primary_key=True),
    Column("pipeline_run_id", UUID(as_uuid=True),
           ForeignKey("pipeline.pipeline_run.id"),
           nullable=False),
    Column("variables_save_path", String, nullable=False),
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
    Column("setup_script_path", String, nullable=True),
    Column("default_config", JSONB, nullable=True),
    Column("type", String, nullable=False),
    Column("created_at", DateTime(timezone=True),
           default=datetime.now(timezone.utc), nullable=False),
    Column("updated_at", DateTime(timezone=True),
           default=datetime.now(timezone.utc),
           onupdate=datetime.now(timezone.utc), nullable=False),
    CheckConstraint(function_type_constraint),
    schema="pipeline"
)

function_input_structure = Table(
    "function_input_structure",
    metadata,
    Column("id", UUID(as_uuid=True),
           default=uuid.uuid4,
           primary_key=True),
    Column("function_id", UUID(as_uuid=True),
           ForeignKey("pipeline.function.id"),
           nullable=False),
    Column("structure_id", String, nullable=False),
    Column("name", String, nullable=False),
    Column("description", String, nullable=True),
    Column("required", Boolean, nullable=False),
    CheckConstraint(structure_constraint),
    Column("created_at", DateTime(timezone=True),
           default=datetime.now(timezone.utc), nullable=False),
    Column("updated_at", DateTime(timezone=True),
           default=datetime.now(timezone.utc),
           onupdate=datetime.now(timezone.utc), nullable=False),
    schema="pipeline"
)


function_output_structure = Table(
    "function_output_structure",
    metadata,
    Column("id", UUID(as_uuid=True),
           default=uuid.uuid4,
           primary_key=True),
    Column("name", String, nullable=False),
    Column("function_id", UUID(as_uuid=True),
           ForeignKey("pipeline.function.id"),
           nullable=False),
    Column("structure_id", String, nullable=False),
    Column("created_at", DateTime(timezone=True),
           default=datetime.now(timezone.utc), nullable=False),
    Column("updated_at", DateTime(timezone=True),
           default=datetime.now(timezone.utc),
           onupdate=datetime.now(timezone.utc), nullable=False),
    Column("description", String, nullable=True),
    CheckConstraint(structure_constraint),
    schema="pipeline"
)


function_output_variable = Table(
    "function_output_variable",
    metadata,
    Column("id", UUID(as_uuid=True),
           default=uuid.uuid4,
           primary_key=True),
    Column("name", String, nullable=False),
    Column("function_id", UUID(as_uuid=True),
           ForeignKey("pipeline.function.id"),
           nullable=False),
    Column("python_type", String, nullable=False),
    Column("created_at", DateTime(timezone=True),
           default=datetime.now(timezone.utc), nullable=False),
    Column("updated_at", DateTime(timezone=True),
           default=datetime.now(timezone.utc),
           onupdate=datetime.now(timezone.utc), nullable=False),
    Column("description", String, nullable=True),
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
    Column("position", Integer, nullable=False),
    Column("config", JSONB, nullable=True),
    Column("created_at", DateTime(timezone=True),
           default=datetime.now(timezone.utc), nullable=False),
    Column("updated_at", DateTime(timezone=True),
           default=datetime.now(timezone.utc),
           onupdate=datetime.now(timezone.utc), nullable=False),
    schema="pipeline"
)


model_modality_constraint = "modality IN ('time_series', 'tabular', 'multimodal', 'image', 'text', 'audio', 'video')"
model_source_constraint = "source IN ('github', 'pypi', 'gitlab', 'huggingface', 'local')"


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
    Column("public", Boolean, nullable=False),
    Column("modality", String, nullable=False),
    Column("source", String, nullable=False),
    Column("programming_language_with_version", String, nullable=False),
    Column("setup_script_path", String, nullable=True),
    Column("default_config", JSONB, nullable=True),
    CheckConstraint(model_modality_constraint),
    CheckConstraint(model_source_constraint),
    Column("created_at", DateTime(timezone=True),
           default=datetime.now(timezone.utc), nullable=False),
    Column("updated_at", DateTime(timezone=True),
           default=datetime.now(timezone.utc),
           onupdate=datetime.now(timezone.utc), nullable=False),
    schema="pipeline"
)


model_task_constraint = "task IN ('forecasting', 'classification', 'regression', 'clustering', 'anomaly_detection', 'generation', 'segmentation')"


model_task = Table(
    "model_task",
    metadata,
    Column("model_id", UUID(as_uuid=True),
           ForeignKey("pipeline.model.id"),
           primary_key=True,
           nullable=False),
    Column("task", String, nullable=False, primary_key=True),
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
    CheckConstraint(model_task_constraint),
    schema="pipeline"
)
