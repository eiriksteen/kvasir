import uuid
from datetime import timezone, datetime
from sqlalchemy import Column, String, ForeignKey, Table, UUID, DateTime
from sqlalchemy.dialects.postgresql import JSONB

from synesis_api.database.core import metadata


# The pipeline entity is the overarching object (where the final pipeline doesn't need to be defined yet)
# To make a pipeline runnable, we "compile" / "index" it from the defined code
# The code is either defined by the agent or by the user
pipeline = Table(
    "pipeline",
    metadata,
    Column("id", UUID(as_uuid=True),
           default=uuid.uuid4,
           primary_key=True),
    Column("user_id", UUID(as_uuid=True),
           ForeignKey("auth.users.id"),
           nullable=False),
    Column("name", String, nullable=False),
    Column("description", String, nullable=True),
    Column("created_at", DateTime(timezone=True),
           default=datetime.now(timezone.utc), nullable=False),
    Column("updated_at", DateTime(timezone=True),
           default=datetime.now(timezone.utc),
           onupdate=datetime.now(timezone.utc), nullable=False),
    schema="pipeline"
)


# "Compiled" pipeline
pipeline_implementation = Table(
    "pipeline_implementation",
    metadata,
    Column("id",
           UUID(as_uuid=True),
           ForeignKey("pipeline.pipeline.id"),
           default=uuid.uuid4,
           primary_key=True),
    Column("python_function_name", String, nullable=False),
    Column("docstring", String, nullable=False),
    Column("description", String, nullable=True),
    Column("args_schema", JSONB, nullable=False),
    Column("default_args", JSONB, nullable=False),
    Column("output_variables_schema", JSONB, nullable=False),
    Column("implementation_script_path", String, nullable=False),
    Column("created_at", DateTime(timezone=True),
           default=datetime.now(timezone.utc), nullable=False),
    Column("updated_at", DateTime(timezone=True),
           default=datetime.now(timezone.utc),
           onupdate=datetime.now(timezone.utc), nullable=False),
    schema="pipeline"
)


pipeline_run = Table(
    "pipeline_run",
    metadata,
    Column("id", UUID(as_uuid=True),
           default=uuid.uuid4,
           primary_key=True),
    Column("pipeline_id", UUID(as_uuid=True),
           ForeignKey("pipeline.pipeline.id"),
           nullable=False),
    Column("name", String, nullable=True),
    Column("description", String, nullable=True),
    Column("status", String, nullable=False),
    Column("args", JSONB, nullable=True),
    # For storing metrics etc, will be updated in real time
    Column("output_variables", JSONB, nullable=True),
    Column("execution_command", String, nullable=True),
    Column("terminal_output", String, nullable=True),
    Column("start_time", DateTime(timezone=True), nullable=False),
    Column("end_time", DateTime(timezone=True), nullable=True),
    Column("created_at", DateTime(timezone=True),
           default=datetime.now(timezone.utc), nullable=False),
    Column("updated_at", DateTime(timezone=True),
           default=datetime.now(timezone.utc),
           onupdate=datetime.now(timezone.utc), nullable=False),
    schema="pipeline"
)
