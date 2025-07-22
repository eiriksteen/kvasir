import uuid
from sqlalchemy import Column, String, ForeignKey, Table, UUID, DateTime, func
from sqlalchemy.dialects.postgresql import BYTEA
from synesis_api.database.core import metadata


local_directory_data_source = Table(
    "local_directory_data_source",
    metadata,
    Column("id",
           UUID(as_uuid=True),
           default=uuid.uuid4,
           primary_key=True),
    Column("user_id",
           UUID(as_uuid=True),
           ForeignKey("auth.users.id"),
           nullable=False),
    Column("description", String, nullable=True),
    Column("directory_name", String, nullable=False),
    Column("save_path", String, nullable=False),
    Column("created_at", DateTime(timezone=True),
           nullable=False, default=func.now()),
    schema="data_integration"
)


local_directory_file = Table(
    "local_directory_file",
    metadata,
    Column("id",
           UUID(as_uuid=True),
           default=uuid.uuid4,
           primary_key=True),
    Column("directory_id",
           UUID(as_uuid=True),
           ForeignKey("data_integration.local_directory_data_source.id"),
           nullable=False),
    Column("file_name", String, nullable=False),
    Column("file_path", String, nullable=False),
    Column("file_type", String, nullable=False),
    Column("description", String, nullable=True),
    Column("created_at", DateTime(timezone=True),
           nullable=False, default=func.now()),
    schema="data_integration"
)


data_integration_job_local_input = Table(
    "data_integration_job_local_input",
    metadata,
    Column("job_id",
           UUID(as_uuid=True),
           ForeignKey("jobs.job.id"),
           primary_key=True),
    Column("target_dataset_description", String, nullable=False),
    Column("directory_id",
           UUID(as_uuid=True),
           ForeignKey("data_integration.local_directory_data_source.id"),
           nullable=False),
    Column("created_at", DateTime(timezone=True),
           nullable=False, default=func.now()),
    schema="data_integration"
)


data_integration_job_result = Table(
    "data_integration_job_result",
    metadata,
    Column("job_id",
           UUID(as_uuid=True),
           ForeignKey("jobs.job.id"),
           primary_key=True),
    Column("dataset_id", UUID(as_uuid=True), nullable=False),
    Column("code_explanation", String, nullable=False),
    Column("python_code_path", String, nullable=False),
    schema="data_integration"
)
