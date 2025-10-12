import uuid
from sqlalchemy import Column, String, ForeignKey, Table, UUID, Float, JSON
from sqlalchemy import Column, String, ForeignKey, Table, UUID, DateTime, Boolean


from synesis_api.database.core import metadata
from synesis_api.database.core import metadata

analysis_object = Table(
    "analysis_object",
    metadata,
    Column("id", UUID(as_uuid=True),
           primary_key=True,
           default=uuid.uuid4),
    Column("project_id", UUID(as_uuid=True),
           ForeignKey("project.project.id"),
           nullable=False),
    Column("user_id", UUID(as_uuid=True),
           ForeignKey("auth.users.id"),
           nullable=False),
    Column("name", String, nullable=False),
    Column("description", String, nullable=True),
    Column("created_at", DateTime, nullable=False),
    Column("report_generated", Boolean, nullable=False,
           default=False),  # TODO: delete?
    Column("notebook_id", UUID(as_uuid=True), nullable=False),
    schema="analysis",
)

notebook = Table(
    "notebook",
    metadata,
    Column("id", UUID(as_uuid=True),
           primary_key=True,
           default=uuid.uuid4),
    schema="analysis",
)

notebook_section = Table(
    "notebook_section",
    metadata,
    Column("id", UUID(as_uuid=True),
           primary_key=True,
           default=uuid.uuid4),
    Column("notebook_id", UUID(as_uuid=True),
           ForeignKey("analysis.notebook.id"),
           nullable=False),
    Column("section_name", String, nullable=False),
    Column("section_description", String, nullable=True),
    # 'analysis_result' or 'notebook_section'
    Column("next_type", String, nullable=True),
    Column("next_id", UUID(as_uuid=True), nullable=True),
    Column("parent_section_id", UUID(as_uuid=True),
           ForeignKey("analysis.notebook_section.id"),
           nullable=True),
    schema="analysis",
)

analysis_status_message = Table(
    "analysis_status_message",
    metadata,
    Column("id", UUID(as_uuid=True),
           primary_key=True,
           default=uuid.uuid4),
    Column("run_id", UUID(as_uuid=True),
           ForeignKey("runs.run.id"),
           nullable=False),
    Column("type", String, nullable=False),
    Column("message", String, nullable=False),
    Column("created_at", DateTime, nullable=False),
    Column("analysis_result_id", UUID(as_uuid=True),
           ForeignKey("analysis.analysis_result.id"),
           nullable=False),
    schema="analysis",
)


analysis_result = Table(
    "analysis_result",
    metadata,
    Column("id", UUID(as_uuid=True),
           primary_key=True,
           default=uuid.uuid4),
    Column("analysis", String, nullable=False),
    Column("python_code", String, nullable=True),
    Column("output_variable", String, nullable=True),
    Column("input_variable", String, nullable=True),
    Column("section_id", UUID(as_uuid=True), ForeignKey(
        "analysis.notebook_section.id"), nullable=True,),
    # 'analysis_result' or 'notebook_section'
    Column("next_type", String, nullable=True),
    Column("next_id", UUID(as_uuid=True), nullable=True),
    schema="analysis",
)

analysis_result_dataset = Table(
    "analysis_result_dataset",
    metadata,
    Column("id", UUID(as_uuid=True),
           primary_key=True,
           default=uuid.uuid4),
    Column("analysis_result_id", UUID(as_uuid=True),
           ForeignKey("analysis.analysis_result.id"),
           nullable=False),
    Column("dataset_id", UUID(as_uuid=True),
           ForeignKey("data_objects.dataset.id"),
           nullable=False),
    schema="analysis",
)

analysis_result_data_source = Table(
    "analysis_result_data_source",
    metadata,
    Column("id", UUID(as_uuid=True),
           primary_key=True,
           default=uuid.uuid4),
    Column("analysis_result_id", UUID(as_uuid=True),
           ForeignKey("analysis.analysis_result.id"),
           nullable=False),
    Column("data_source_id", UUID(as_uuid=True),
           ForeignKey("data_sources.data_source.id"),
           nullable=False),
    schema="analysis",
)

plot = Table(
    'plot',
    metadata,
    Column('id', UUID, primary_key=True, default=uuid.uuid4),
    Column('analysis_result_id', UUID, ForeignKey(
        'analysis.analysis_result.id'), nullable=False),
    Column('plot_config', JSON, nullable=False),
    schema='analysis',
)


table = Table(
    'table',
    metadata,
    Column('id', UUID, primary_key=True, default=uuid.uuid4),
    Column('analysis_result_id', UUID, ForeignKey(
        'analysis.analysis_result.id'), nullable=False),
    Column('table_config', JSON, nullable=False),
    schema='analysis',
)
