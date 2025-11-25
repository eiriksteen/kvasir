import uuid
from datetime import datetime, timezone
from sqlalchemy import Column, ForeignKey, Table, UUID, DateTime, UniqueConstraint, String, Float

from synesis_api.database.core import metadata


# =============================================================================
# Node Models
# =============================================================================

entity_node = Table(
    "entity_node",
    metadata,
    Column("id", UUID(as_uuid=True), primary_key=True, nullable=False),
    Column("name", String, nullable=False),
    Column("x_position", Float, nullable=False),
    Column("y_position", Float, nullable=False),
    Column("entity_type", String, nullable=False),
    Column("description", String, nullable=True),
    Column("created_at", DateTime(timezone=True),
           default=datetime.now(timezone.utc), nullable=False),
    Column("updated_at", DateTime(timezone=True),
           default=datetime.now(timezone.utc),
           onupdate=datetime.now(timezone.utc), nullable=False),
    schema="entity_graph"
)


node_group = Table(
    "node_group",
    metadata,
    Column("id", UUID(as_uuid=True), primary_key=True,
           default=uuid.uuid4, nullable=False),
    Column("name", String, nullable=False),
    Column("description", String, nullable=True),
    Column("python_package_name", String, nullable=True),
    Column("created_at", DateTime(timezone=True),
           default=datetime.now(timezone.utc), nullable=False),
    Column("updated_at", DateTime(timezone=True),
           default=datetime.now(timezone.utc),
           onupdate=datetime.now(timezone.utc), nullable=False),
    schema="entity_graph"
)


node_in_group = Table(
    "node_in_group",
    metadata,
    Column("node_id", UUID(as_uuid=True),
           ForeignKey("entity_graph.entity_node.id"), primary_key=True, nullable=False),
    Column("node_group_id", UUID(as_uuid=True),
           ForeignKey("entity_graph.node_group.id"), primary_key=True, nullable=False),
    Column("created_at", DateTime(timezone=True),
           default=datetime.now(timezone.utc), nullable=False),
    Column("updated_at", DateTime(timezone=True),
           default=datetime.now(timezone.utc),
           onupdate=datetime.now(timezone.utc), nullable=False),
    schema="entity_graph"
)


# =============================================================================
# Dataset Associations
# =============================================================================


dataset_from_data_source = Table(
    "dataset_from_data_source",
    metadata,
    Column("data_source_id", UUID(as_uuid=True), ForeignKey(
        "data_sources.data_source.id"), primary_key=True, nullable=False),
    Column("dataset_id", UUID(as_uuid=True), ForeignKey(
        "data_objects.dataset.id"), primary_key=True, nullable=False),
    Column("created_at", DateTime(timezone=True),
           default=datetime.now(timezone.utc), nullable=False),
    Column("updated_at", DateTime(timezone=True),
           default=datetime.now(timezone.utc),
           onupdate=datetime.now(timezone.utc), nullable=False),
    schema="entity_graph"
)


# =============================================================================
# Pipeline Associations
# =============================================================================

# Pipeline Supported Inputs (what entities can be used as pipeline inputs)
data_source_supported_in_pipeline = Table(
    "data_source_supported_in_pipeline",
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
    schema="entity_graph"
)


dataset_supported_in_pipeline = Table(
    "dataset_supported_in_pipeline",
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
    schema="entity_graph"
)


model_instantiated_supported_in_pipeline = Table(
    "model_instantiated_supported_in_pipeline",
    metadata,
    Column("model_instantiated_id", UUID(as_uuid=True),
           ForeignKey("model.model_instantiated.id"), primary_key=True, nullable=False),
    Column("pipeline_id", UUID(as_uuid=True),
           ForeignKey("pipeline.pipeline.id"), primary_key=True, nullable=False),
    Column("created_at", DateTime(timezone=True),
           default=datetime.now(timezone.utc), nullable=False),
    Column("updated_at", DateTime(timezone=True),
           default=datetime.now(timezone.utc),
           onupdate=datetime.now(timezone.utc), nullable=False),
    schema="entity_graph"
)


# Pipeline Run Input Associations
dataset_in_pipeline_run = Table(
    "dataset_in_pipeline_run",
    metadata,
    Column("pipeline_run_id", UUID(as_uuid=True),
           ForeignKey("pipeline.pipeline_run.id"), primary_key=True, nullable=False),
    Column("dataset_id", UUID(as_uuid=True),
           ForeignKey("data_objects.dataset.id"), primary_key=True, nullable=False),
    Column("created_at", DateTime(timezone=True),
           default=datetime.now(timezone.utc), nullable=False),
    Column("updated_at", DateTime(timezone=True),
           default=datetime.now(timezone.utc),
           onupdate=datetime.now(timezone.utc), nullable=False),
    schema="entity_graph"
)


data_source_in_pipeline_run = Table(
    "data_source_in_pipeline_run",
    metadata,
    Column("pipeline_run_id", UUID(as_uuid=True),
           ForeignKey("pipeline.pipeline_run.id"), primary_key=True, nullable=False),
    Column("data_source_id", UUID(as_uuid=True),
           ForeignKey("data_sources.data_source.id"), primary_key=True, nullable=False),
    Column("created_at", DateTime(timezone=True),
           default=datetime.now(timezone.utc), nullable=False),
    Column("updated_at", DateTime(timezone=True),
           default=datetime.now(timezone.utc),
           onupdate=datetime.now(timezone.utc), nullable=False),
    schema="entity_graph"
)


model_instantiated_in_pipeline_run = Table(
    "model_instantiated_in_pipeline_run",
    metadata,
    Column("pipeline_run_id", UUID(as_uuid=True),
           ForeignKey("pipeline.pipeline_run.id"), primary_key=True, nullable=False),
    Column("model_instantiated_id", UUID(as_uuid=True),
           ForeignKey("model.model_instantiated.id"), primary_key=True, nullable=False),
    Column("created_at", DateTime(timezone=True),
           default=datetime.now(timezone.utc), nullable=False),
    Column("updated_at", DateTime(timezone=True),
           default=datetime.now(timezone.utc),
           onupdate=datetime.now(timezone.utc), nullable=False),
    schema="entity_graph"
)


# Pipeline Run Output Associations
pipeline_run_output_dataset = Table(
    "pipeline_run_output_dataset",
    metadata,
    Column("pipeline_run_id", UUID(as_uuid=True),
           ForeignKey("pipeline.pipeline_run.id"), primary_key=True, nullable=False),
    Column("dataset_id", UUID(as_uuid=True),
           ForeignKey("data_objects.dataset.id"), primary_key=True, nullable=False),
    Column("created_at", DateTime(timezone=True),
           default=datetime.now(timezone.utc), nullable=False),
    Column("updated_at", DateTime(timezone=True),
           default=datetime.now(timezone.utc),
           onupdate=datetime.now(timezone.utc), nullable=False),
    # Unique constraint on dataset_id since a dataset can only be output from one pipeline run
    UniqueConstraint(
        "dataset_id", name="uq_pipeline_run_output_dataset_dataset_id"),
    schema="entity_graph"
)


pipeline_run_output_model_entity = Table(
    "pipeline_run_output_model_entity",
    metadata,
    Column("pipeline_run_id", UUID(as_uuid=True),
           ForeignKey("pipeline.pipeline_run.id"), primary_key=True, nullable=False),
    Column("model_instantiated_id", UUID(as_uuid=True),
           ForeignKey("model.model_instantiated.id"), primary_key=True, nullable=False),
    Column("created_at", DateTime(timezone=True),
           default=datetime.now(timezone.utc), nullable=False),
    Column("updated_at", DateTime(timezone=True),
           default=datetime.now(timezone.utc),
           onupdate=datetime.now(timezone.utc), nullable=False),
    # Unique constraint on model_instantiated_id since a model entity can only be output from one pipeline run
    UniqueConstraint(
        "model_instantiated_id", name="uq_pipeline_run_output_model_entity_model_entity_id"),
    schema="entity_graph"
)


pipeline_run_output_data_source = Table(
    "pipeline_run_output_data_source",
    metadata,
    Column("pipeline_run_id", UUID(as_uuid=True),
           ForeignKey("pipeline.pipeline_run.id"), primary_key=True, nullable=False),
    Column("data_source_id", UUID(as_uuid=True),
           ForeignKey("data_sources.data_source.id"), primary_key=True, nullable=False),
    Column("created_at", DateTime(timezone=True),
           default=datetime.now(timezone.utc), nullable=False),
    Column("updated_at", DateTime(timezone=True),
           default=datetime.now(timezone.utc),
           onupdate=datetime.now(timezone.utc), nullable=False),
    # Unique constraint on data_source_id since a data source can only be output from one pipeline run
    UniqueConstraint("data_source_id",
                     name="uq_pipeline_run_output_data_source_data_source_id"),
    schema="entity_graph"
)


# =============================================================================
# Analysis Input Associations
# =============================================================================

dataset_in_analysis = Table(
    "dataset_in_analysis",
    metadata,
    Column("analysis_id", UUID(as_uuid=True),
           ForeignKey("analysis.analysis.id"),
           primary_key=True,
           nullable=False),
    Column("dataset_id", UUID(as_uuid=True),
           ForeignKey("data_objects.dataset.id"),
           primary_key=True,
           nullable=False),
    Column("created_at", DateTime(timezone=True),
           default=datetime.now(timezone.utc), nullable=False),
    Column("updated_at", DateTime(timezone=True),
           default=datetime.now(timezone.utc),
           onupdate=datetime.now(timezone.utc), nullable=False),
    schema="entity_graph",
)


data_source_in_analysis = Table(
    "data_source_in_analysis",
    metadata,
    Column("analysis_id", UUID(as_uuid=True),
           ForeignKey("analysis.analysis.id"),
           primary_key=True,
           nullable=False),
    Column("data_source_id", UUID(as_uuid=True),
           ForeignKey("data_sources.data_source.id"),
           primary_key=True,
           nullable=False),
    Column("created_at", DateTime(timezone=True),
           default=datetime.now(timezone.utc), nullable=False),
    Column("updated_at", DateTime(timezone=True),
           default=datetime.now(timezone.utc),
           onupdate=datetime.now(timezone.utc), nullable=False),
    schema="entity_graph",
)


model_instantiated_in_analysis = Table(
    "model_instantiated_in_analysis",
    metadata,
    Column("analysis_id", UUID(as_uuid=True),
           ForeignKey("analysis.analysis.id"),
           primary_key=True,
           nullable=False),
    Column("model_instantiated_id", UUID(as_uuid=True),
           ForeignKey("model.model_instantiated.id"),
           primary_key=True,
           nullable=False),
    Column("created_at", DateTime(timezone=True),
           default=datetime.now(timezone.utc), nullable=False),
    Column("updated_at", DateTime(timezone=True),
           default=datetime.now(timezone.utc),
           onupdate=datetime.now(timezone.utc), nullable=False),
    schema="entity_graph",
)
