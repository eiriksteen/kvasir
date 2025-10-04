import uuid
from sqlalchemy import Column, String, ForeignKey, Table, UUID, Float
from synesis_api.database.core import metadata

# Base node table that other node types will inherit from
node = Table(
    "node",
    metadata,
    Column("id", UUID(as_uuid=True), primary_key=True, default=uuid.uuid4),
    Column("project_id", UUID(as_uuid=True), ForeignKey(
        "project.project.id"), nullable=False),
    Column("x_position", Float, nullable=False),
    Column("y_position", Float, nullable=False),
    Column("type", String(255), nullable=False),
    schema="node"
)

data_source_node = Table(
    "data_source_node",
    metadata,
    Column("id", UUID(as_uuid=True), ForeignKey(
        "node.node.id"), primary_key=True),
    Column("data_source_id", UUID(as_uuid=True), ForeignKey(
        "data_sources.data_source.id"), nullable=False),
    schema="node"
)


# Dataset node table
dataset_node = Table(
    "dataset_node",
    metadata,
    Column("id", UUID(as_uuid=True), ForeignKey(
        "node.node.id"), primary_key=True),
    Column("dataset_id", UUID(as_uuid=True), ForeignKey(
        "data_objects.dataset.id"), nullable=False),
    schema="node"
)

# Analysis node table
analysis_node = Table(
    "analysis_node",
    metadata,
    Column("id", UUID(as_uuid=True), ForeignKey(
        "node.node.id"), primary_key=True),
    Column("analysis_id", UUID(as_uuid=True), ForeignKey(
        "analysis.analysis_objects.id"), nullable=False),
    schema="node"
)

# Pipeline node table
pipeline_node = Table(
    "pipeline_node",
    metadata,
    Column("id", UUID(as_uuid=True), ForeignKey(
        "node.node.id"), primary_key=True),
    Column("pipeline_id", UUID(as_uuid=True), ForeignKey(
        "pipeline.pipeline.id"), nullable=False),
    schema="node"
)

# Model entity node table
model_entity_node = Table(
    "model_entity_node",
    metadata,
    Column("id", UUID(as_uuid=True), ForeignKey(
        "node.node.id"), primary_key=True),
    Column("model_entity_id", UUID(as_uuid=True), ForeignKey(
        "model.model_entity.id"), nullable=False),
    schema="node"
)
