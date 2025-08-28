import uuid
from datetime import datetime, timezone
from sqlalchemy import Column, Integer, String, DateTime, ForeignKey, Table, UUID, CheckConstraint, Boolean
from sqlalchemy.dialects.postgresql import JSONB
from synesis_api.database.core import metadata
from synesis_data_structures.time_series.definitions import get_first_level_structure_ids

# Build the constraint string with proper quotes
structure_ids = get_first_level_structure_ids()
structure_constraint = "structure_type IN (" + \
    ", ".join(f"'{id}'" for id in structure_ids) + ")"


# TODO: Add fields for data quality (e.g. missing values, outliers, etc.)


# Overarching dataset table that dataframes are linked to
dataset = Table(
    "dataset",
    metadata,
    Column("id", UUID(as_uuid=True), primary_key=True),
    Column("user_id", UUID, ForeignKey("auth.users.id"), nullable=False),
    Column("description", String, nullable=False),
    Column("name", String, nullable=False),
    # Type will reference the modality, options are "time_series", "document", "image", "video", "multimodal"
    Column("modality", String, nullable=False),
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
    # Role is primary, annotated, or derived
    # Primary is the main data, annotated is ground truth targets, and derived is a computed quantity
    # Primary must be a data object of the primary modality of the dataset, meaning either a time series, image, document, or video, etc, but not a mask, aggregation, or similar quantity
    Column("role", String, nullable=False),
    # Data structure type indicates the actual data structure: time_series, time_series_mask, time_series_aggregation, etc.
    Column("structure_type", String, nullable=False),
    Column("created_at", DateTime(timezone=True),
           default=datetime.now(timezone.utc), nullable=False),
    Column("updated_at", DateTime(timezone=True), default=datetime.now(timezone.utc),
           onupdate=datetime.now(timezone.utc), nullable=False),
    # Ensure the structure type is a valid first level structure id
    CheckConstraint(structure_constraint),
    schema="data_objects"
)


# To store the source data objects of a derived object
derived_object_source = Table(
    "derived_object_source",
    metadata,
    Column("id", UUID(as_uuid=True), ForeignKey(
        "data_objects.data_object.id"), primary_key=True, default=uuid.uuid4),
    Column("derived_object_id", UUID, ForeignKey(
        "data_objects.data_object.id"), nullable=False),
    Column("original_object_id", UUID, ForeignKey(
        "data_objects.data_object.id"), nullable=False),
    Column("created_at", DateTime(timezone=True),
           default=datetime.now(timezone.utc), nullable=False),
    Column("updated_at", DateTime(timezone=True), default=datetime.now(timezone.utc),
           onupdate=datetime.now(timezone.utc), nullable=False),
    schema="data_objects"
)


feature = Table(
    "feature",
    metadata,
    Column("name", String, primary_key=True, nullable=False),
    Column("unit", String, nullable=True),
    Column("description", String, nullable=False),
    # One of numerical, categorical
    Column("type", String, nullable=False),
    # One of continuous, discrete
    Column("subtype", String, nullable=False),
    # One of ratio, interval, ordinal, nominal
    Column("scale", String, nullable=False),
    Column("created_at", DateTime(timezone=True),
           default=datetime.now(timezone.utc), nullable=False),
    Column("updated_at", DateTime(timezone=True), default=datetime.now(timezone.utc),
           onupdate=datetime.now(timezone.utc), nullable=False),
    schema="data_objects"
)


feature_in_group = Table(
    "feature_in_group",
    metadata,
    Column("group_id", UUID(as_uuid=True), ForeignKey(
        "data_objects.object_group.id"), primary_key=True, nullable=False),
    Column("feature_name", String, ForeignKey(
        "data_objects.feature.name"), primary_key=True, nullable=False),
    # data or metadata
    Column("source", String, nullable=False),
    # For categorical features, the integer the label is mapped to in the actual data
    Column("category_id", Integer, nullable=True),
    Column("created_at", DateTime(timezone=True),
           default=datetime.now(timezone.utc), nullable=False),
    Column("updated_at", DateTime(timezone=True), default=datetime.now(timezone.utc),
           onupdate=datetime.now(timezone.utc), nullable=False),
    CheckConstraint("source IN ('data', 'metadata')"),
    schema="data_objects"
)


# Metadata of a single (multivariate) time series
# Flexible structure, can be used to define forecasts and masks on existing series as well (can use additional_variables to tie it to the original series)
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
    schema="data_objects"
)


# Time series aggregation is to compute a single value from a time series, for example the mean or a class label of a segment
time_series_aggregation = Table(
    "time_series_aggregation",
    metadata,
    Column("id", UUID(as_uuid=True), ForeignKey(
        "data_objects.data_object.id"), primary_key=True, default=uuid.uuid4),
    Column("is_multi_series_computation", Boolean, nullable=False),
    schema="data_objects"
)


time_series_aggregation_input = Table(
    "time_series_aggregation_input",
    metadata,
    Column("id", UUID(as_uuid=True), ForeignKey(
        "data_objects.data_object.id"), primary_key=True, default=uuid.uuid4),
    Column("time_series_id", UUID, ForeignKey(
        "data_objects.time_series.id"), nullable=False),
    Column("aggregation_id", UUID, ForeignKey(
        "data_objects.time_series_aggregation.id"), nullable=False),
    Column("input_feature_name", String, nullable=False),
    Column("start_timestamp", DateTime(timezone=True), nullable=False),
    Column("end_timestamp", DateTime(timezone=True), nullable=False),
    Column("created_at", DateTime(timezone=True),
           default=datetime.now(timezone.utc), nullable=False),
    Column("updated_at", DateTime(timezone=True), default=datetime.now(timezone.utc),
           onupdate=datetime.now(timezone.utc), nullable=False),
    CheckConstraint("start_timestamp < end_timestamp"),
    schema="data_objects"
)
