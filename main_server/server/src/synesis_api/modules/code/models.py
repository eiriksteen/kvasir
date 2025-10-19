import uuid
from sqlalchemy import Column, String, ForeignKey, Table, UUID, DateTime, func

from synesis_api.database.core import metadata


script = Table(
    "script",
    metadata,
    Column("id", UUID(as_uuid=True), primary_key=True, default=uuid.uuid4),
    Column("user_id", UUID(as_uuid=True),
           ForeignKey("auth.users.id"),
           nullable=False),
    Column("output", String, nullable=True),
    Column("error", String, nullable=True),
    Column("path", String, nullable=False),
    Column("filename", String, nullable=False),
    # Only for python scripts
    Column("module_path", String, nullable=True),
    # function, model, pipeline, data_integration, analysis
    Column("type", String, nullable=False),
    Column("created_at", DateTime(timezone=True),
           nullable=False, default=func.now()),
    Column("updated_at", DateTime(timezone=True),
           nullable=False, default=func.now(), onupdate=func.now()),
    schema="code"
    # TODO: Many more fields can be added
)
