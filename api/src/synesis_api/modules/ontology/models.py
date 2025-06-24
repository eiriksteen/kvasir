from datetime import datetime, timezone
from sqlalchemy import Column, Integer, String, DateTime, ForeignKey, Table, UUID
from sqlalchemy.dialects.postgresql import ARRAY
from synesis_api.database.core import metadata
import uuid


# Base dataset table that other dataset types will inherit from
dataset = Table(
    "dataset",
    metadata,
    Column("id", UUID(as_uuid=True),
           ForeignKey("jobs.jobs.id"),
           primary_key=True),
    Column("user_id", UUID, ForeignKey("auth.users.id"), nullable=False),
    Column("description", String, nullable=False),
    Column("name", String, nullable=False),
    Column("created_at", DateTime(timezone=True),
           default=datetime.now(timezone.utc), nullable=False),
    Column("updated_at", DateTime(timezone=True), default=datetime.now(timezone.utc),
           onupdate=datetime.now(timezone.utc), nullable=False),
    schema="ontology"
)

dataset_metadata = Table(
    "dataset_metadata",
    metadata,
    Column("dataset_id", UUID, ForeignKey(
        "ontology.dataset.id"), primary_key=True),
    Column("column_names", ARRAY(String), nullable=False),
    Column("column_types", ARRAY(String), nullable=False),
    Column("num_columns", Integer, nullable=False),
    schema="ontology"
)

tabular_dataset = Table(
    "tabular_dataset",
    metadata,
    Column("id", UUID, ForeignKey("ontology.dataset.id"), primary_key=True),
    Column("features", ARRAY(String), nullable=False),
    Column("num_features", Integer, nullable=False),
    schema="ontology"
)

time_series = Table(
    "time_series",
    metadata,
    Column("id", UUID, primary_key=True, default=uuid.uuid4),
    Column("original_id", String, nullable=True),
    Column("num_timestamps", Integer, nullable=False),
    Column("start_timestamp", DateTime(timezone=True), nullable=False),
    Column("end_timestamp", DateTime(timezone=True), nullable=False),
    Column("dataset_id", UUID, ForeignKey(
        "ontology.dataset.id"), nullable=False),
    schema="ontology"
)

time_series_dataset = Table(
    "time_series_dataset",
    metadata,
    Column("id", UUID, ForeignKey("ontology.dataset.id"), primary_key=True),
    Column("num_series", Integer, nullable=False),
    Column("num_features", Integer, nullable=False),
    Column("features", ARRAY(String), nullable=False),
    Column("index_first_level", String, nullable=False),
    Column("index_second_level", String, nullable=True),
    Column("avg_num_timestamps", Integer, nullable=False),
    Column("max_num_timestamps", Integer, nullable=False),
    Column("min_num_timestamps", Integer, nullable=False),
    schema="ontology"
)
