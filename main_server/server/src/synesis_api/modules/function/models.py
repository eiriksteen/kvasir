import uuid
from datetime import timezone, datetime
from sqlalchemy import Column, String, ForeignKey, Table, UUID, DateTime, Boolean, CheckConstraint, Integer, Float, UniqueConstraint
from sqlalchemy.dialects.postgresql import JSONB
from pgvector.sqlalchemy import Vector

from synesis_api.database.core import metadata
from synesis_api.app_secrets import EMBEDDING_DIM


function_type_constraint = "type IN ('inference', 'training', 'computation', 'tool')"


# The function is defined once, and then multiple versions of it can be created (the function table)
# For new queries, we will always use the latest version of the function
# During experimentation and usage, when flaws of the functions are found, we create a new version
function_definition = Table(
    "function_definition",
    metadata,
    Column("id", UUID(as_uuid=True),
           default=uuid.uuid4,
           primary_key=True),
    Column("name", String, nullable=False),
    Column("type", String, nullable=False),
    Column("args_dataclass_name", String, nullable=False),
    Column("input_dataclass_name", String, nullable=False),
    Column("output_dataclass_name", String, nullable=False),
    Column("output_variables_dataclass_name", String, nullable=False),
    Column("created_at", DateTime(timezone=True),
           default=datetime.now(timezone.utc), nullable=False),
    Column("updated_at", DateTime(timezone=True),
           default=datetime.now(timezone.utc),
           onupdate=datetime.now(timezone.utc), nullable=False),
    CheckConstraint(function_type_constraint),
    UniqueConstraint("name"),
    schema="function"
)


function = Table(
    "function",
    metadata,
    Column("id", UUID(as_uuid=True),
           default=uuid.uuid4,
           primary_key=True),
    Column("definition_id", UUID(as_uuid=True),
           ForeignKey("function.function_definition.id"),
           nullable=False),
    Column("version", Integer, nullable=False),
    Column("args_schema", JSONB, nullable=False),
    Column("output_variables_schema", JSONB, nullable=False),
    Column("newest_update_description", String, nullable=False),
    Column("description", String, nullable=False),
    Column("docstring", String, nullable=False),
    Column("embedding", Vector(dim=EMBEDDING_DIM), nullable=False),
    Column("python_function_name", String, nullable=False),
    Column("implementation_script_path", String, nullable=False),
    Column("setup_script_path", String, nullable=True),
    Column("default_args", JSONB, nullable=True),
    Column("created_at", DateTime(timezone=True),
           default=datetime.now(timezone.utc), nullable=False),
    Column("updated_at", DateTime(timezone=True),
           default=datetime.now(timezone.utc),
           onupdate=datetime.now(timezone.utc), nullable=False),
    schema="function"
)
