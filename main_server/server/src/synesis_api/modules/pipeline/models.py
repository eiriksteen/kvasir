import uuid
from datetime import timezone, datetime
from sqlalchemy import Column, String, ForeignKey, Table, UUID, DateTime, CheckConstraint, UniqueConstraint
from sqlalchemy.dialects.postgresql import JSONB
from pgvector.sqlalchemy import Vector

from synesis_api.database.core import metadata
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
    Column("python_function_name", String, nullable=False),
    Column("docstring", String, nullable=False),
    Column("description", String, nullable=True),
    Column("args", JSONB, nullable=True),
    Column("args_schema", JSONB, nullable=False),
    Column("output_variables_schema", JSONB, nullable=False),
    Column("args_dataclass_name", String, nullable=False),
    Column("input_dataclass_name", String, nullable=False),
    Column("output_dataclass_name", String, nullable=False),
    Column("output_variables_dataclass_name", String, nullable=False),
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


object_group_in_pipeline = Table(
    "object_group_in_pipeline",
    metadata,
    Column("pipeline_id", UUID(as_uuid=True),
           ForeignKey("pipeline.pipeline.id"),
           primary_key=True,
           nullable=False),
    Column("object_group_id", UUID(as_uuid=True),
           ForeignKey("data_objects.object_group.id"),
           primary_key=True,
           nullable=False),
    Column("code_variable_name", String, nullable=False),
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
    Column("code_variable_name", String, nullable=False),
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


pipeline_output_object_group_definition = Table(
    "pipeline_output_object_group_definition",
    metadata,
    Column("id", UUID(as_uuid=True),
           default=uuid.uuid4,
           primary_key=True),
    Column("pipeline_id", UUID(as_uuid=True),
           ForeignKey("pipeline.pipeline.id"),
           nullable=False),
    Column("name", String, nullable=False),
    Column("structure_id", String, nullable=False),
    Column("description", String, nullable=True),
    Column("output_entity_id_name", String, nullable=False),
    Column("created_at", DateTime(timezone=True),
           default=datetime.now(timezone.utc), nullable=False),
    Column("updated_at", DateTime(timezone=True),
           default=datetime.now(timezone.utc),
           onupdate=datetime.now(timezone.utc), nullable=False),
    CheckConstraint(structure_constraint),
    UniqueConstraint("pipeline_id", "name"),
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


pipeline_graph_node = Table(
    "pipeline_graph_node",
    metadata,
    Column("id", UUID(as_uuid=True),
           default=uuid.uuid4,
           primary_key=True),
    Column("type", String, nullable=False),
    CheckConstraint(f"type IN ('dataset', 'function', 'model_entity')"),
    Column("pipeline_id", UUID(as_uuid=True),
           ForeignKey("pipeline.pipeline.id"),
           nullable=False),
    Column("created_at", DateTime(timezone=True),
           default=datetime.now(timezone.utc), nullable=False),
    Column("updated_at", DateTime(timezone=True),
           default=datetime.now(timezone.utc),
           onupdate=datetime.now(timezone.utc), nullable=False),
    schema="pipeline"
)


pipeline_graph_edge = Table(
    "pipeline_graph_edge",
    metadata,
    Column("from_node_id", UUID(as_uuid=True),
           ForeignKey("pipeline.pipeline_graph_node.id"),
           primary_key=True,
           nullable=False),
    Column("to_node_id", UUID(as_uuid=True),
           ForeignKey("pipeline.pipeline_graph_node.id"),
           primary_key=True,
           nullable=False),
    Column("created_at", DateTime(timezone=True),
           default=datetime.now(timezone.utc), nullable=False),
    Column("updated_at", DateTime(timezone=True),
           default=datetime.now(timezone.utc),
           onupdate=datetime.now(timezone.utc), nullable=False),
    schema="pipeline"
)


pipeline_graph_dataset_node = Table(
    "pipeline_graph_dataset_node",
    metadata,
    Column("id", UUID(as_uuid=True),
           ForeignKey("pipeline.pipeline_graph_node.id"),
           primary_key=True,
           nullable=False),
    Column("dataset_id", UUID(as_uuid=True),
           ForeignKey("data_objects.dataset.id"),
           nullable=False),
    Column("created_at", DateTime(timezone=True),
           default=datetime.now(timezone.utc), nullable=False),
    Column("updated_at", DateTime(timezone=True),
           default=datetime.now(timezone.utc),
           onupdate=datetime.now(timezone.utc), nullable=False),
    schema="pipeline"
)


pipeline_graph_function_node = Table(
    "pipeline_graph_function_node",
    metadata,
    Column("id", UUID(as_uuid=True),
           ForeignKey("pipeline.pipeline_graph_node.id"),
           primary_key=True,
           nullable=False),
    Column("function_id", UUID(as_uuid=True),
           ForeignKey("function.function.id"),
           nullable=False),
    Column("created_at", DateTime(timezone=True),
           default=datetime.now(timezone.utc), nullable=False),
    Column("updated_at", DateTime(timezone=True),
           default=datetime.now(timezone.utc),
           onupdate=datetime.now(timezone.utc), nullable=False),
    schema="pipeline"
)


pipeline_graph_model_entity_node = Table(
    "pipeline_graph_model_entity_node",
    metadata,
    Column("id", UUID(as_uuid=True),
           ForeignKey("pipeline.pipeline_graph_node.id"),
           primary_key=True,
           nullable=False),
    Column("model_entity_id", UUID(as_uuid=True),
           ForeignKey("model.model_entity.id"),
           nullable=False),
    Column("function_type", String, nullable=False),
    CheckConstraint(f"function_type IN ('training', 'inference')"),
    Column("created_at", DateTime(timezone=True),
           default=datetime.now(timezone.utc), nullable=False),
    Column("updated_at", DateTime(timezone=True),
           default=datetime.now(timezone.utc),
           onupdate=datetime.now(timezone.utc), nullable=False),
    schema="pipeline"
)
