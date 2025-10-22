import uuid
from sqlalchemy.dialects.postgresql import JSONB
from sqlalchemy import Column, String, ForeignKey, Table, UUID, DateTime, func, CheckConstraint, BigInteger, Integer
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
    Column("created_at", DateTime(timezone=True),
           nullable=False, default=func.now()),
    Column("updated_at", DateTime(timezone=True),
           nullable=False, default=func.now(), onupdate=func.now()),
    schema="data_sources"
)


tabular_file_data_source = Table(
    "tabular_file_data_source",
    metadata,
    Column("id",
           UUID(as_uuid=True),
           ForeignKey("data_sources.data_source.id"),
           primary_key=True),
    Column("file_name", String, nullable=False),
    Column("file_path", String, nullable=False),
    Column("file_type", String, nullable=False),
    Column("file_size_bytes", BigInteger, nullable=False),
    Column("num_rows", Integer, nullable=False),
    Column("num_columns", Integer, nullable=False),
    Column("content_preview", String, nullable=False),
    Column("json_schema", JSONB, nullable=False),
    Column("created_at", DateTime(timezone=True),
           nullable=False, default=func.now()),
    Column("updated_at", DateTime(timezone=True),
           nullable=False, default=func.now(), onupdate=func.now()),
    schema="data_sources"
)


key_value_file_data_source = Table(
    "key_value_file_data_source",
    metadata,
    Column("id", UUID(as_uuid=True), ForeignKey(
        "data_sources.data_source.id"), primary_key=True),
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


data_source_analysis = Table(
    "data_source_analysis",
    metadata,
    Column("id", UUID(as_uuid=True), ForeignKey(
        "data_sources.data_source.id"), primary_key=True),
    Column("data_source_id", UUID(as_uuid=True), ForeignKey(
        "data_sources.data_source.id"), nullable=False),
    Column("content_description", String, nullable=False),
    Column("quality_description", String, nullable=False),
    Column("eda_summary", String, nullable=False),
    Column("cautions", String, nullable=False),
    Column("created_at", DateTime(timezone=True),
           nullable=False, default=func.now()),
    Column("updated_at", DateTime(timezone=True),
           nullable=False, default=func.now(), onupdate=func.now()),
    schema="data_sources"
)
