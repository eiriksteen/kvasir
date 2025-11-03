import uuid
from datetime import datetime, timezone
from sqlalchemy import Column, ForeignKey, Table, UUID, DateTime, func

from synesis_api.database.core import metadata


# =============================================================================
# Data Source Associations
# =============================================================================

data_source_from_pipeline = Table(
    "data_source_from_pipeline",
    metadata,
    Column("data_source_id", UUID(as_uuid=True),
           ForeignKey("data_sources.data_source.id"),
           primary_key=True),
    Column("pipeline_id", UUID(as_uuid=True),
           ForeignKey("pipeline.pipeline.id"),
           primary_key=True),
    Column("created_at", DateTime(timezone=True),
           nullable=False, default=func.now()),
    Column("updated_at", DateTime(timezone=True),
           nullable=False, default=func.now(), onupdate=func.now()),
    schema="entity_graph"
)


# =============================================================================
# Dataset Associations
# =============================================================================

dataset_from_pipeline = Table(
    "dataset_from_pipeline",
    metadata,
    Column("pipeline_id", UUID, ForeignKey(
        "pipeline.pipeline.id"), primary_key=True, nullable=False),
    Column("dataset_id", UUID, ForeignKey(
        "data_objects.dataset.id"), primary_key=True, nullable=False),
    # If we have done any runs
    Column("pipeline_run_id", UUID, ForeignKey(
        "pipeline.pipeline_run.id"), nullable=True),
    schema="entity_graph"
)


dataset_from_data_source = Table(
    "dataset_from_data_source",
    metadata,
    Column("data_source_id", UUID, ForeignKey(
        "data_sources.data_source.id"), primary_key=True, nullable=False),
    Column("dataset_id", UUID, ForeignKey(
        "data_objects.dataset.id"), primary_key=True, nullable=False),
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


model_entity_supported_in_pipeline = Table(
    "model_entity_supported_in_pipeline",
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


model_entity_in_pipeline_run = Table(
    "model_entity_in_pipeline_run",
    metadata,
    Column("pipeline_run_id", UUID(as_uuid=True),
           ForeignKey("pipeline.pipeline_run.id"), primary_key=True, nullable=False),
    Column("model_entity_id", UUID(as_uuid=True),
           ForeignKey("model.model_entity.id"), primary_key=True, nullable=False),
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
    schema="entity_graph"
)


pipeline_run_output_model_entity = Table(
    "pipeline_run_output_model_entity",
    metadata,
    Column("pipeline_run_id", UUID(as_uuid=True),
           ForeignKey("pipeline.pipeline_run.id"), primary_key=True, nullable=False),
    Column("model_entity_id", UUID(as_uuid=True),
           ForeignKey("model.model_entity.id"), primary_key=True, nullable=False),
    Column("created_at", DateTime(timezone=True),
           default=datetime.now(timezone.utc), nullable=False),
    Column("updated_at", DateTime(timezone=True),
           default=datetime.now(timezone.utc),
           onupdate=datetime.now(timezone.utc), nullable=False),
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
    schema="entity_graph"
)


# =============================================================================
# Analysis Input Associations
# =============================================================================

dataset_in_analysis = Table(
    "dataset_in_analysis",
    metadata,
    Column("id", UUID(as_uuid=True),
           primary_key=True,
           default=uuid.uuid4),
    Column("analysis_id", UUID(as_uuid=True),
           ForeignKey("analysis.analysis.id"),
           nullable=False),
    Column("dataset_id", UUID(as_uuid=True),
           ForeignKey("data_objects.dataset.id"),
           nullable=False),
    schema="entity_graph",
)


data_source_in_analysis = Table(
    "data_source_in_analysis",
    metadata,
    Column("id", UUID(as_uuid=True),
           primary_key=True,
           default=uuid.uuid4),
    Column("analysis_id", UUID(as_uuid=True),
           ForeignKey("analysis.analysis.id"),
           nullable=False),
    Column("data_source_id", UUID(as_uuid=True),
           ForeignKey("data_sources.data_source.id"),
           nullable=False),
    schema="entity_graph",
)


model_entity_in_analysis = Table(
    "model_entity_in_analysis",
    metadata,
    Column("id", UUID(as_uuid=True),
           primary_key=True,
           default=uuid.uuid4),
    Column("analysis_id", UUID(as_uuid=True),
           ForeignKey("analysis.analysis.id"),
           nullable=False),
    Column("model_entity_id", UUID(as_uuid=True),
           ForeignKey("model.model_entity.id"),
           nullable=False),
    schema="entity_graph",
)


analysis_from_past_analysis = Table(
    "analysis_from_past_analysis",
    metadata,
    Column("id", UUID(as_uuid=True),
           primary_key=True,
           default=uuid.uuid4),
    Column("analysis_id", UUID(as_uuid=True),
           ForeignKey("analysis.analysis.id"),
           nullable=False),
    Column("past_analysis_id", UUID(as_uuid=True),
           ForeignKey("analysis.analysis.id"),
           nullable=False),
    schema="entity_graph",
)
