import uuid
from sqlalchemy import Column, String, DateTime, ForeignKey, Table, UUID
from ..database.core import metadata


model_jobs = Table(
    "model_jobs",
    metadata,
    Column("id", UUID(as_uuid=True), primary_key=True, default=uuid.uuid4),
    Column("status", String, nullable=False),
    Column("user_id", UUID(as_uuid=True),
           ForeignKey("users.id"), nullable=False),
    Column("api_key_id", UUID(as_uuid=True),
           ForeignKey("user_api_keys.id"), nullable=False),
    Column("started_at", DateTime, nullable=False),
    Column("completed_at", DateTime, nullable=True),
)