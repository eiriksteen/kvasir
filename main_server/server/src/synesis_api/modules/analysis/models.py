from sqlalchemy import Column, String, ForeignKey, Table, UUID, Float
from synesis_api.database.core import metadata
from sqlalchemy import Column, String, ForeignKey, Table, UUID, DateTime, Boolean
from synesis_api.database.core import metadata
import uuid

# New analysis_objects table
analysis_objects = Table(
    "analysis_objects",
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
    Column("report_generated", Boolean, nullable=False, default=False), # TODO: delete?
    Column("notebook_id", UUID(as_uuid=True), nullable=False),
    schema="analysis",
)

# New notebooks table
notebooks = Table(
    "notebooks",
    metadata,
    Column("id", UUID(as_uuid=True),
           primary_key=True,
           default=uuid.uuid4),
    schema="analysis",
)

# New notebook_sections table
notebook_sections = Table(
    "notebook_sections",
    metadata,
    Column("id", UUID(as_uuid=True),
           primary_key=True,
           default=uuid.uuid4),
    Column("notebook_id", UUID(as_uuid=True),
           ForeignKey("analysis.notebooks.id"),
           nullable=False),
    Column("section_name", String, nullable=False),
    Column("section_description", String, nullable=True),
    Column("next_type", String, nullable=True),  # 'analysis_result' or 'notebook_section'
    Column("next_id", UUID(as_uuid=True), nullable=True),
    Column("parent_section_id", UUID(as_uuid=True),
           ForeignKey("analysis.notebook_sections.id"),
           nullable=True),
    schema="analysis",
)

analysis_status_messages = Table(
    "analysis_status_messages",
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
           ForeignKey("analysis.analysis_results.id"),
           nullable=False),
    schema="analysis",
)

# TODO: Delete?
analysis_objects_datasets = Table(
    "analysis_objects_datasets",
    metadata,
    Column("id", UUID(as_uuid=True),
           primary_key=True,
           default=uuid.uuid4),
    Column("analysis_object_id", UUID(as_uuid=True),
           ForeignKey("analysis.analysis_objects.id"),
           nullable=False),
    Column("dataset_id", UUID(as_uuid=True),
           ForeignKey("data_objects.dataset.id"),
           nullable=False),
    schema="analysis",
)

analysis_results = Table(
    "analysis_results",
    metadata,
    Column("id", UUID(as_uuid=True),
           primary_key=True,
           default=uuid.uuid4),
    Column("analysis", String, nullable=False),
    Column("python_code", String, nullable=True),
    Column("output_variable", String, nullable=True),
    Column("input_variable", String, nullable=True),
    Column("section_id", UUID(as_uuid=True), ForeignKey("analysis.notebook_sections.id"), nullable=True,),
    Column("next_type", String, nullable=True),  # 'analysis_result' or 'notebook_section'
    Column("next_id", UUID(as_uuid=True), nullable=True),
    schema="analysis",
)

analysis_results_datasets = Table(
    "analysis_results_datasets",
    metadata,
    Column("id", UUID(as_uuid=True),
           primary_key=True,
           default=uuid.uuid4),
    Column("analysis_result_id", UUID(as_uuid=True),
           ForeignKey("analysis.analysis_results.id"),
           nullable=False),
    Column("dataset_id", UUID(as_uuid=True),
           ForeignKey("data_objects.dataset.id"),
           nullable=False),
    schema="analysis",
)

analysis_results_data_sources = Table(
    "analysis_results_data_sources",
    metadata,
    Column("id", UUID(as_uuid=True),
           primary_key=True,
           default=uuid.uuid4),
    Column("analysis_result_id", UUID(as_uuid=True),
           ForeignKey("analysis.analysis_results.id"),
           nullable=False),
    Column("data_source_id", UUID(as_uuid=True),
           ForeignKey("data_sources.data_source.id"),
           nullable=False),
    schema="analysis",
)

analysis_result_runs = Table(
    "analysis_result_runs",
    metadata,
    Column("id", UUID(as_uuid=True),
           primary_key=True,
           default=uuid.uuid4),
    Column("analysis_result_id", UUID(as_uuid=True),
           ForeignKey("analysis.analysis_results.id"),
           nullable=False),
    Column("run_id", UUID(as_uuid=True),
           ForeignKey("runs.run.id"),
           nullable=False),
    schema="analysis",
)