import uuid
from datetime import datetime, timezone
from sqlalchemy import Column, ForeignKey, Table, UUID, DateTime, UniqueConstraint, String, Float

from synesis_api.database.core import metadata


project = Table(
    "project",
    metadata,
    Column("id", UUID(as_uuid=True), primary_key=True, default=uuid.uuid4),
    Column("name", String, nullable=False),
    Column("view_port_x", Float, nullable=False, default=0.0),
    Column("view_port_y", Float, nullable=False, default=0.0),
    Column("view_port_zoom", Float, nullable=False, default=1.0),
    Column("user_id", UUID(as_uuid=True), ForeignKey(
        "auth.users.id"), nullable=False),
    Column("description", String, nullable=True),
    Column("created_at", DateTime(timezone=True),
           default=datetime.now(timezone.utc), nullable=False),
    Column("updated_at", DateTime(timezone=True),
           default=datetime.now(timezone.utc),
           onupdate=datetime.now(timezone.utc), nullable=False),
    schema="project",
)
