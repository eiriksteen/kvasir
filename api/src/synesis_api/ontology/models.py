from datetime import datetime
from sqlalchemy import Column, Integer, String, DateTime, ForeignKey, Table, UUID
from sqlalchemy.dialects.postgresql import ARRAY
from ..database.core import metadata
import uuid


feature_data = Table(
    "feature_data",
    metadata,
    Column("id", UUID, primary_key=True, default=uuid.uuid4),
    Column("description", String, nullable=False),
    Column("features", ARRAY(String), nullable=False),
    Column("num_features", Integer, nullable=False),
    Column("dataset_id", UUID, ForeignKey(
        "time_series_dataset.id"), nullable=False),
    Column("created_at", DateTime, default=datetime.now(), nullable=False),
    Column("updated_at", DateTime, default=datetime.now(),
           onupdate=datetime.now(), nullable=False)
)

time_series = Table(
    "time_series",
    metadata,
    Column("id", UUID, primary_key=True, default=uuid.uuid4),
    Column("original_id", String, nullable=True),
    Column("description", String, nullable=False),
    Column("features", ARRAY(String), nullable=False),
    Column("num_timestamps", Integer, nullable=False),
    Column("num_features", Integer, nullable=False),
    Column("start_timestamp", DateTime, nullable=False),
    Column("end_timestamp", DateTime, nullable=False),
    Column("dataset_id", UUID, ForeignKey(
        "time_series_dataset.id"), nullable=False),
    Column("created_at", DateTime, default=datetime.now(), nullable=False),
    Column("updated_at", DateTime, default=datetime.now(),
           onupdate=datetime.now(), nullable=False)
)


time_series_dataset = Table(
    "time_series_dataset",
    metadata,
    Column("id", UUID, primary_key=True, default=uuid.uuid4),
    Column("user_id", UUID, ForeignKey("users.id"), nullable=False),
    Column("description", String, nullable=False),
    Column("name", String, nullable=False),
    Column("num_series", Integer, nullable=False),
    Column("num_features", Integer, nullable=False),
    Column("index_first_level", String, nullable=False),
    Column("index_second_level", String, nullable=True),
    Column("avg_num_timestamps", Integer, nullable=False),
    Column("max_num_timestamps", Integer, nullable=False),
    Column("min_num_timestamps", Integer, nullable=False),
    Column("created_at", DateTime, default=datetime.now(), nullable=False),
    Column("updated_at", DateTime, default=datetime.now(),
           onupdate=datetime.now(), nullable=False)
)
