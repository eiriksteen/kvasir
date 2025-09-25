import uuid
from sqlalchemy import Column, String, ForeignKey, Table, UUID, DateTime, func, CheckConstraint, BigInteger, Integer, Boolean
from pgvector.sqlalchemy import Vector

from synesis_api.database.core import metadata
from synesis_api.app_secrets import EMBEDDING_DIM

# TODO: Should maybe have a separate table for possible data sources
SUPPORTED_MODEL_SOURCES = ["github", "pypi", "gitlab", "huggingface", "local"]


# Build the constraint string with proper quotes
model_source_constraint = "type IN (" + \
    ", ".join(f"'{id}'" for id in SUPPORTED_MODEL_SOURCES) + ")"


model_source = Table(
    "model_source",
    metadata,
    Column("id",
           UUID(as_uuid=True),
           default=uuid.uuid4,
           primary_key=True),
    Column("user_id",
           UUID(as_uuid=True),
           ForeignKey("auth.users.id"),
           nullable=False),
    Column("type", String, nullable=False),
    Column("name", String, nullable=False),
    Column("description", String, nullable=False),
    Column("public", Boolean, nullable=False),
    Column("embedding", Vector(dim=EMBEDDING_DIM), nullable=False),
    Column("created_at", DateTime(timezone=True),
           nullable=False, default=func.now()),
    Column("updated_at", DateTime(timezone=True),
           nullable=False, default=func.now(), onupdate=func.now()),
    CheckConstraint(model_source_constraint),
    schema="model_sources"
)


pypi_model_source = Table(
    "pypi_model_source",
    metadata,
    Column("id",
           UUID(as_uuid=True),
           ForeignKey("model_sources.model_source.id"),
           primary_key=True),
    Column("package_name", String, nullable=False),
    Column("package_version", String, nullable=False),
    Column("created_at", DateTime(timezone=True),
           nullable=False, default=func.now()),
    Column("updated_at", DateTime(timezone=True),
           nullable=False, default=func.now(), onupdate=func.now()),
    schema="model_sources"
)


# TODO: Add more
