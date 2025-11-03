import uuid
from sqlalchemy.dialects.postgresql import JSONB
from sqlalchemy import Column, String, ForeignKey, Table, UUID, DateTime, func, BigInteger, Integer
from synesis_api.database.core import metadata


data_source = Table(
    "data_source",
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
    Column("additional_variables", JSONB, nullable=True),
    Column("created_at", DateTime(timezone=True),
           nullable=False, default=func.now()),
    Column("updated_at", DateTime(timezone=True),
           nullable=False, default=func.now(), onupdate=func.now()),
    schema="data_sources"
)


file_data_source = Table(
    "file_data_source",
    metadata,
    Column("id",
           UUID(as_uuid=True),
           ForeignKey("data_sources.data_source.id"),
           primary_key=True),
    Column("file_name", String, nullable=False),
    Column("file_path", String, nullable=False),
    Column("file_type", String, nullable=False),
    Column("file_size_bytes", BigInteger, nullable=False),
    Column("created_at", DateTime(timezone=True),
           nullable=False, default=func.now()),
    Column("updated_at", DateTime(timezone=True),
           nullable=False, default=func.now(), onupdate=func.now()),
    schema="data_sources"
)
