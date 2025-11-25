import uuid
from sqlalchemy import Table, Column, String, Boolean, DateTime, func, ForeignKey
from sqlalchemy.dialects.postgresql import UUID
from kvasir_api.database.core import metadata

users = Table(
    "users",
    metadata,
    Column("id", UUID(as_uuid=True), primary_key=True, default=uuid.uuid4),
    Column("email", String, nullable=False, unique=True),
    Column("name", String, nullable=False),
    Column("affiliation", String, nullable=False, default="Unknown"),
    Column("role", String, nullable=False, default="Unknown"),
    Column("disabled", Boolean, nullable=False, default=False),
    Column("google_id", String, nullable=True, unique=True),
    Column("hashed_password", String, nullable=True),
    Column("created_at", DateTime(timezone=True),
           nullable=False, default=func.now()),
    Column("updated_at", DateTime(timezone=True), nullable=False,
           default=func.now(), onupdate=func.now()),
    schema="auth"
)

user_api_keys = Table(
    "user_api_keys",
    metadata,
    Column("id", UUID(as_uuid=True), primary_key=True, default=uuid.uuid4),
    Column("user_id", UUID(as_uuid=True),
           ForeignKey("auth.users.id"), nullable=False),
    Column("key", String, nullable=False, unique=True),
    Column("expires_at", DateTime(timezone=True), nullable=False),
    Column("created_at", DateTime(timezone=True), default=func.now()),
    Column("updated_at", DateTime(timezone=True), default=func.now(),
           onupdate=func.now()),
    schema="auth"
)
