import uuid
from datetime import datetime, timezone
from sqlalchemy import Column, ForeignKey, Table, UUID, DateTime, UniqueConstraint, String, Float

from kvasir_api.database.core import metadata


# =============================================================================
# Node Models
# =============================================================================

node = Table(
    "node",
    metadata,
    Column("id", UUID(as_uuid=True), primary_key=True, nullable=False),
    Column("name", String, nullable=False),
    Column("x_position", Float, nullable=False),
    Column("y_position", Float, nullable=False),
    Column("node_type", String, nullable=False),
    Column("description", String, nullable=True),
    Column("created_at", DateTime(timezone=True),
           default=datetime.now(timezone.utc), nullable=False),
    Column("updated_at", DateTime(timezone=True),
           default=datetime.now(timezone.utc),
           onupdate=datetime.now(timezone.utc), nullable=False),
    schema="entity_graph"
)


leaf_node = Table(
    "leaf_node",
    metadata,
    Column("id", UUID(as_uuid=True), ForeignKey("entity_graph.node.id"),
           primary_key=True,
           default=uuid.uuid4, nullable=False),
    Column("entity_id", UUID(as_uuid=True), nullable=False),
    Column("entity_type", String, nullable=False),
    Column("created_at", DateTime(timezone=True),
           default=datetime.now(timezone.utc), nullable=False),
    Column("updated_at", DateTime(timezone=True),
           default=datetime.now(timezone.utc), onupdate=datetime.now(timezone.utc), nullable=False),
    schema="entity_graph"
)


branch_node = Table(
    "branch_node",
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


parent_child_relation = Table(
    "parent_child_relation",
    metadata,
    Column("child_id", UUID(as_uuid=True),
           ForeignKey("entity_graph.node.id"), primary_key=True, nullable=False),
    Column("parent_id", UUID(as_uuid=True),
           ForeignKey("entity_graph.node.id"), primary_key=True, nullable=False),
    Column("created_at", DateTime(timezone=True),
           default=datetime.now(timezone.utc), nullable=False),
    Column("updated_at", DateTime(timezone=True),
           default=datetime.now(timezone.utc),
           onupdate=datetime.now(timezone.utc), nullable=False),
    schema="entity_graph"
)


edge = Table(
    "edge",
    metadata,
    Column("from_entity_id", UUID(as_uuid=True),
           primary_key=True, nullable=False),
    Column("to_entity_id", UUID(as_uuid=True),
           primary_key=True, nullable=False),
    Column("created_at", DateTime(timezone=True),
           default=datetime.now(timezone.utc), nullable=False),
    Column("updated_at", DateTime(timezone=True),
           default=datetime.now(timezone.utc),
           onupdate=datetime.now(timezone.utc), nullable=False),
    schema="entity_graph"
)
