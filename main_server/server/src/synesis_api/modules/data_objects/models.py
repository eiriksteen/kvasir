import uuid
from datetime import datetime, timezone
from sqlalchemy import Column, Integer, String, DateTime, ForeignKey, Table, UUID
from sqlalchemy.dialects.postgresql import JSONB
from synesis_api.database.core import metadata

# TODO: Add fields for data quality (e.g. missing values, outliers, etc.)


# Overarching dataset table that dataframes are linked to
dataset = Table(
    "dataset",
    metadata,
    Column("id", UUID(as_uuid=True), primary_key=True),
    Column("user_id", UUID, ForeignKey("auth.users.id"), nullable=False),
    Column("description", String, nullable=False),
    Column("name", String, nullable=False),
    Column("additional_variables", JSONB, nullable=True),
    Column("created_at", DateTime(timezone=True),
           default=datetime.now(timezone.utc), nullable=False),
    Column("updated_at", DateTime(timezone=True), default=datetime.now(timezone.utc),
           onupdate=datetime.now(timezone.utc), nullable=False),
    schema="data_objects"
)


data_object = Table(
    "data_object",
    metadata,
    Column("id", UUID(as_uuid=True), primary_key=True, default=uuid.uuid4),
    # For now, enforce that every data object is part of a group
    Column("group_id", UUID, ForeignKey(
        "data_objects.object_group.id"), nullable=True),
    Column("original_id", String, nullable=True),
    Column("name", String, nullable=True),
    Column("description", String, nullable=True),
    # Flexible field, can for example store object metadata
    Column("additional_variables", JSONB, nullable=True),
    Column("created_at", DateTime(timezone=True),
           default=datetime.now(timezone.utc), nullable=False),
    Column("updated_at", DateTime(timezone=True), default=datetime.now(timezone.utc),
           onupdate=datetime.now(timezone.utc), nullable=False),
    schema="data_objects",
)


object_group = Table(
    "object_group",
    metadata,
    Column("id", UUID(as_uuid=True), primary_key=True, default=uuid.uuid4),
    # For now enforce the group can only be part of a single dataset
    Column("dataset_id", UUID, ForeignKey(
        "data_objects.dataset.id"), nullable=False),
    Column("name", String, nullable=False),
    Column("original_id_name", String, nullable=True),
    Column("description", String, nullable=False),
    # Modality indicates the actual data structure: time_series, tabular, etc.
    Column("modality", String, nullable=False),
    Column("additional_variables", JSONB, nullable=True),
    Column("created_at", DateTime(timezone=True),
           default=datetime.now(timezone.utc), nullable=False),
    Column("updated_at", DateTime(timezone=True), default=datetime.now(timezone.utc),
           onupdate=datetime.now(timezone.utc), nullable=False),
    schema="data_objects"
)


time_series = Table(
    "time_series",
    metadata,
    Column("id", UUID(as_uuid=True), ForeignKey(
        "data_objects.data_object.id"), primary_key=True, default=uuid.uuid4),
    Column("num_timestamps", Integer, nullable=False),
    Column("start_timestamp", DateTime(timezone=True), nullable=False),
    Column("end_timestamp", DateTime(timezone=True), nullable=False),
    # m, h, d, w, y, or irr (irregular)
    Column("sampling_frequency", String, nullable=False),
    Column("timezone", String, nullable=False),
    Column("features_schema", JSONB, nullable=False),
    Column("created_at", DateTime(timezone=True),
           default=datetime.now(timezone.utc), nullable=False),
    Column("updated_at", DateTime(timezone=True), default=datetime.now(timezone.utc),
           onupdate=datetime.now(timezone.utc), nullable=False),
    schema="data_objects"
)


time_series_group = Table(
    "time_series_group",
    metadata,
    Column("id", UUID(as_uuid=True), ForeignKey(
        "data_objects.object_group.id"), primary_key=True, default=uuid.uuid4),
    Column("total_timestamps", Integer, nullable=False),
    Column("number_of_series", Integer, nullable=False),
    Column("sampling_frequency", String, nullable=True),
    Column("timezone", String, nullable=True),
    Column("features_schema", JSONB, nullable=True),
    Column("earliest_timestamp", DateTime(timezone=True), nullable=False),
    Column("latest_timestamp", DateTime(timezone=True), nullable=False),
    Column("created_at", DateTime(timezone=True),
           default=datetime.now(timezone.utc), nullable=False),
    Column("updated_at", DateTime(timezone=True), default=datetime.now(timezone.utc),
           onupdate=datetime.now(timezone.utc), nullable=False),
    schema="data_objects"
)


object_group_from_pipeline = Table(
    "object_group_from_pipeline",
    metadata,
    Column("pipeline_id", UUID, ForeignKey(
        "pipeline.pipeline.id"), primary_key=True, nullable=False),
    Column("object_group_id", UUID, ForeignKey(
        "data_objects.object_group.id"), primary_key=True, nullable=False),
    # If we have done any runs
    Column("pipeline_run_id", UUID, ForeignKey(
        "pipeline.pipeline_run.id"), nullable=True),
    schema="data_objects"
)


object_group_from_data_source = Table(
    "object_group_from_data_source",
    metadata,
    Column("data_source_id", UUID, ForeignKey(
        "data_sources.data_source.id"), primary_key=True, nullable=False),
    Column("object_group_id", UUID, ForeignKey(
        "data_objects.object_group.id"), primary_key=True, nullable=False),
    schema="data_objects"
)
