import uuid
from sqlalchemy import Column, String, ForeignKey, Table, UUID, DateTime, func, CheckConstraint, BigInteger, Integer
from synesis_api.database.core import metadata


# TODO: Should maybe have a separate table for possible data sources
SUPPORTED_DATA_SOURCES = ["TabularFile"]


# Build the constraint string with proper quotes
source_constraint = "type IN (" + \
    ", ".join(f"'{id}'" for id in SUPPORTED_DATA_SOURCES) + ")"


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
    # Description and content preview will be filled in by the data integration agent,
    # so that we don't have to redo basic analysis every time we run extraction from a data source
    Column("description", String, nullable=True),
    Column("quality_description", String, nullable=True),
    Column("content_preview", String, nullable=True),
    Column("created_at", DateTime(timezone=True),
           nullable=False, default=func.now()),
    CheckConstraint(source_constraint),
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


tabular_file_data_source = Table(
    "tabular_file_data_source",
    metadata,
    Column("id",
           UUID(as_uuid=True),
           ForeignKey("data_sources.file_data_source.id"),
           primary_key=True),
    Column("num_rows", Integer, nullable=False),
    Column("num_columns", Integer, nullable=False),
    Column("created_at", DateTime(timezone=True),
           nullable=False, default=func.now()),
    Column("updated_at", DateTime(timezone=True),
           nullable=False, default=func.now(), onupdate=func.now()),
    schema="data_sources"
)


feature_in_tabular_file = Table(
    "feature_in_tabular_file",
    metadata,
    Column("feature_name", String, ForeignKey(
        "data_objects.feature.name"), primary_key=True, nullable=False),
    Column("tabular_file_id", UUID(as_uuid=True), ForeignKey(
        "data_sources.tabular_file_data_source.id"), primary_key=True, nullable=False),
    Column("created_at", DateTime(timezone=True),
           nullable=False, default=func.now()),
    Column("updated_at", DateTime(timezone=True),
           nullable=False, default=func.now(), onupdate=func.now()),
    schema="data_sources"
)

data_source_group = Table(
    "data_source_group",
    metadata,
    Column("id",
           UUID(as_uuid=True),
           default=uuid.uuid4,
           primary_key=True),
    Column("name", String, nullable=False),
    Column("description", String, nullable=True),
    Column("created_at", DateTime(timezone=True),
           nullable=False, default=func.now()),
    Column("updated_at", DateTime(timezone=True),
           nullable=False, default=func.now(), onupdate=func.now()),
    schema="data_sources"
)


data_source_in_group = Table(
    "data_source_in_group",
    metadata,
    Column("group_id",
           UUID(as_uuid=True),
           ForeignKey("data_sources.data_source_group.id"),
           primary_key=True),
    Column("data_source_id",
           UUID(as_uuid=True),
           ForeignKey("data_sources.data_source.id"),
           nullable=False),
    Column("created_at", DateTime(timezone=True),
           nullable=False, default=func.now()),
    Column("updated_at", DateTime(timezone=True),
           nullable=False, default=func.now(), onupdate=func.now()),
    schema="data_sources"
)


subgroup = Table(
    "subgroup",
    metadata,
    Column("id",
           UUID(as_uuid=True),
           default=uuid.uuid4,
           primary_key=True),
    Column("parent_group_id",
           UUID(as_uuid=True),
           ForeignKey("data_sources.data_source_group.id"),
           nullable=False),
    Column("child_group_id",
           UUID(as_uuid=True),
           ForeignKey("data_sources.data_source_group.id"),
           nullable=False),
    Column("created_at", DateTime(timezone=True),
           nullable=False, default=func.now()),
    schema="data_sources"
)
