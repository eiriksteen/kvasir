import uuid
from sqlalchemy import Table, Column, String, Boolean, DateTime, func, ForeignKey
from sqlalchemy.dialects.postgresql import UUID
from synesis_api.database.core import metadata

users = Table(
    "users",
    metadata,
    Column("id", UUID(as_uuid=True), primary_key=True, default=uuid.uuid4),
    Column("email", String, nullable=False, unique=True),
    Column("name", String, nullable=False),
    Column("disabled", Boolean, nullable=False, default=False),
    Column("hashed_password", String, nullable=False),
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
