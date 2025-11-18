import uuid
from datetime import timezone, datetime
from sqlalchemy import Column, String, ForeignKey, Table, UUID, DateTime, Integer, CheckConstraint

from synesis_api.database.core import metadata


analysis = Table(
    "analysis",
    metadata,
    Column("id", UUID(as_uuid=True),
           primary_key=True,
           default=uuid.uuid4),
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
    schema="analysis",
)


analysis_section = Table(
    "analysis_section",
    metadata,
    Column("id", UUID(as_uuid=True),
           primary_key=True,
           default=uuid.uuid4),
    Column("name", String, nullable=False),
    Column("analysis_id", UUID(as_uuid=True),
           ForeignKey("analysis.analysis.id"),
           nullable=False),
    Column("description", String, nullable=True),
    Column("created_at", DateTime(timezone=True),
           default=datetime.now(timezone.utc), nullable=False),
    Column("updated_at", DateTime(timezone=True),
           default=datetime.now(timezone.utc),
           onupdate=datetime.now(timezone.utc), nullable=False),
    schema="analysis",
)


analysis_cell = Table(
    "analysis_cell",
    metadata,
    Column("id", UUID(as_uuid=True),
           primary_key=True,
           default=uuid.uuid4),
    Column("order", Integer, nullable=False),
    Column("type", String, nullable=False),
    Column("section_id", UUID(as_uuid=True),
           ForeignKey("analysis.analysis_section.id"),
           nullable=False),
    Column("created_at", DateTime(timezone=True),
           default=datetime.now(timezone.utc), nullable=False),
    Column("updated_at", DateTime(timezone=True),
           default=datetime.now(timezone.utc),
           onupdate=datetime.now(timezone.utc), nullable=False),
    CheckConstraint("type IN ('markdown', 'code')",
                    name="analysis_cell_type_check"),
    schema="analysis",
)


markdown_cell = Table(
    "markdown_cell",
    metadata,
    Column("id", UUID(as_uuid=True),
           ForeignKey("analysis.analysis_cell.id"),
           primary_key=True),
    Column("markdown", String, nullable=False),
    Column("created_at", DateTime(timezone=True),
           default=datetime.now(timezone.utc), nullable=False),
    Column("updated_at", DateTime(timezone=True),
           default=datetime.now(timezone.utc),
           onupdate=datetime.now(timezone.utc), nullable=False),
    schema="analysis",
)


code_cell = Table(
    "code_cell",
    metadata,
    Column("id", UUID(as_uuid=True),
           ForeignKey("analysis.analysis_cell.id"),
           primary_key=True),
    Column("code", String, nullable=False),
    Column("created_at", DateTime(timezone=True),
           default=datetime.now(timezone.utc), nullable=False),
    Column("updated_at", DateTime(timezone=True),
           default=datetime.now(timezone.utc),
           onupdate=datetime.now(timezone.utc), nullable=False),
    schema="analysis",
)


code_output = Table(
    "code_output",
    metadata,
    Column("id", UUID(as_uuid=True),
           ForeignKey("analysis.code_cell.id"),
           primary_key=True),
    Column("output", String, nullable=False),
    Column("created_at", DateTime(timezone=True),
           default=datetime.now(timezone.utc), nullable=False),
    Column("updated_at", DateTime(timezone=True),
           default=datetime.now(timezone.utc),
           onupdate=datetime.now(timezone.utc), nullable=False),
    schema="analysis",
)


result_image = Table(
    "result_image",
    metadata,
    Column("id", UUID(as_uuid=True),
           primary_key=True,
           default=uuid.uuid4),
    Column("code_cell_id", UUID(as_uuid=True),
           ForeignKey("analysis.code_cell.id"),
           nullable=False),
    Column("image_id", UUID(as_uuid=True),
           ForeignKey("visualization.image.id"),
           nullable=False),
    Column("created_at", DateTime(timezone=True),
           default=datetime.now(timezone.utc), nullable=False),
    Column("updated_at", DateTime(timezone=True),
           default=datetime.now(timezone.utc),
           onupdate=datetime.now(timezone.utc), nullable=False),
    schema="analysis",
)


result_echart = Table(
    "result_echart",
    metadata,
    Column("id", UUID(as_uuid=True),
           primary_key=True,
           default=uuid.uuid4),
    Column("code_cell_id", UUID(as_uuid=True),
           ForeignKey("analysis.code_cell.id"),
           nullable=False),
    Column("echart_id", UUID(as_uuid=True),
           ForeignKey("visualization.echart.id"),
           nullable=False),
    Column("created_at", DateTime(timezone=True),
           default=datetime.now(timezone.utc), nullable=False),
    Column("updated_at", DateTime(timezone=True),
           default=datetime.now(timezone.utc),
           onupdate=datetime.now(timezone.utc), nullable=False),
    schema="analysis",
)


result_table = Table(
    "result_table",
    metadata,
    Column("id", UUID(as_uuid=True),
           primary_key=True,
           default=uuid.uuid4),
    Column("code_cell_id", UUID(as_uuid=True),
           ForeignKey("analysis.code_cell.id"),
           nullable=False),
    Column("table_id", UUID(as_uuid=True),
           ForeignKey("visualization.table.id"),
           nullable=False),
    Column("created_at", DateTime(timezone=True),
           default=datetime.now(timezone.utc), nullable=False),
    Column("updated_at", DateTime(timezone=True),
           default=datetime.now(timezone.utc),
           onupdate=datetime.now(timezone.utc), nullable=False),
    schema="analysis",
)
