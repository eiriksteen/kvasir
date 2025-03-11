from datetime import datetime
from sqlalchemy import Column, Integer, String, DateTime, ForeignKey, Table, UUID
from sqlalchemy.dialects.postgresql import ARRAY
from ..database.core import metadata
import uuid


time_series = Table(
    "time_series",
    metadata,
    Column("id", UUID, primary_key=True, default=uuid.uuid4),
    Column("original_id", String),
    Column("description", String),
    Column("features", ARRAY(String)),
    Column("num_timestamps", Integer),
    Column("num_features", Integer),
    Column("start_timestamp", DateTime),
    Column("end_timestamp", DateTime),
    Column("dataset_id", UUID, ForeignKey("time_series_dataset.id")),
    Column("created_at", DateTime, default=datetime.now()),
    Column("updated_at", DateTime, default=datetime.now(),
           onupdate=datetime.now())
)


time_series_dataset = Table(
    "time_series_dataset",
    metadata,
    Column("id", UUID, primary_key=True, default=uuid.uuid4),
    Column("description", String),
    Column("name", String),
    Column("num_series", Integer),
    Column("num_features", Integer),
    Column("index_first_level", String),
    Column("index_second_level", String, nullable=True),
    Column("avg_num_timestamps", Integer),
    Column("max_num_timestamps", Integer),
    Column("min_num_timestamps", Integer),
    Column("created_at", DateTime, default=datetime.now()),
    Column("updated_at", DateTime, default=datetime.now(),
           onupdate=datetime.now())
)
