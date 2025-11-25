import uuid
from sqlalchemy import Column, String, Table, UUID, DateTime
from datetime import datetime, timezone

from synesis_api.database.core import metadata


image = Table(
    'image',
    metadata,
    Column('id', UUID, primary_key=True, default=uuid.uuid4),
    Column('user_id', UUID, nullable=False),
    Column('image_path', String, nullable=False),
    Column('created_at', DateTime(timezone=True),
           default=datetime.now(timezone.utc), nullable=False),
    Column('updated_at', DateTime(timezone=True), default=datetime.now(
        timezone.utc), onupdate=datetime.now(timezone.utc), nullable=False),
    schema='visualization',
)


echart = Table(
    'echart',
    metadata,
    Column('id', UUID, primary_key=True, default=uuid.uuid4),
    Column('user_id', UUID, nullable=False),
    Column("chart_script_path", String, nullable=False),
    Column('created_at', DateTime(timezone=True),
           default=datetime.now(timezone.utc), nullable=False),
    Column('updated_at', DateTime(timezone=True), default=datetime.now(
        timezone.utc), onupdate=datetime.now(timezone.utc), nullable=False),
    schema='visualization',
)


table = Table(
    'table',
    metadata,
    Column('id', UUID, primary_key=True, default=uuid.uuid4),
    Column('user_id', UUID, nullable=False),
    # Stores project server path to the parquet file of the dataframe corresponding to the table
    Column('table_path', String, nullable=False),
    Column('created_at', DateTime(timezone=True),
           default=datetime.now(timezone.utc), nullable=False),
    Column('updated_at', DateTime(timezone=True), default=datetime.now(
        timezone.utc), onupdate=datetime.now(timezone.utc), nullable=False),
    schema='visualization',
)
