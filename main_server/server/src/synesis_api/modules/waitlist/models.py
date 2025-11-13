import uuid
from datetime import datetime, timezone
from sqlalchemy import Column, String, Table, UUID, DateTime
from synesis_api.database.core import metadata


waitlist = Table(
    "waitlist",
    metadata,
    Column("id", UUID(as_uuid=True), primary_key=True, default=uuid.uuid4),
    Column("email", String, nullable=False, unique=True),
    Column("name", String, nullable=False),
    Column("affiliation", String, nullable=False),
    Column("role", String, nullable=False),
    Column("created_at", DateTime(timezone=True),
           default=datetime.now(timezone.utc), nullable=False),
    schema="waitlist"
)

