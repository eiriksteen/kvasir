from sqlalchemy import Column, String, ForeignKey, Table, UUID
from synesis_api.database.core import metadata
from sqlalchemy import Column, String, ForeignKey, Table, UUID, DateTime, Boolean, Integer
from synesis_api.database.core import metadata
import uuid

analysis_jobs_results = Table(
    "analysis_jobs_results",
    metadata,
    Column("job_id", UUID(as_uuid=True),
           ForeignKey("jobs.jobs.id"),
           primary_key=True),
    Column("basic_eda", String, nullable=True),
    Column("advanced_eda", String, nullable=True),
    Column("independent_eda", String, nullable=True),
    Column("python_code", String, nullable=True),
    Column("ad_hoc", String, nullable=True, default=None),
    Column("dataset_id", UUID(as_uuid=True),
           ForeignKey("integration_jobs_results.dataset_id"),
           nullable=True),
       ForeignKey("jobs.jobs.id"),
       primary_key=True),
    Column("number_of_datasets", Integer, nullable=False),
    Column("number_of_automations", Integer, nullable=False),
    Column("analysis_plan", UUID(as_uuid=True), ForeignKey("analysis.analysis_plans.job_id"), nullable=False),
    Column("created_at", DateTime, nullable=False),
    Column("pdf_created", Boolean, nullable=False),
    Column("pdf_s3_path", String, nullable=True),
    Column("user_id", UUID(as_uuid=True), ForeignKey("auth.users.id"), nullable=False),
    schema="analysis",
)


analysis_jobs_datasets = Table(
    "analysis_jobs_datasets",
    metadata,
    Column("id", UUID(as_uuid=True),
           primary_key=True,
           default=uuid.uuid4),
    Column("job_id", UUID(as_uuid=True),
           ForeignKey("jobs.jobs.id"),
           nullable=False),
    Column("dataset_id", UUID(as_uuid=True),
           ForeignKey("ontology.dataset.id"),
           nullable=False),
    schema="analysis",
)

analysis_jobs_automations = Table( 
    "analysis_jobs_automations",
    metadata,
    Column("id", UUID(as_uuid=True),
           primary_key=True,
           default=uuid.uuid4),
    Column("job_id", UUID(as_uuid=True),
           ForeignKey("jobs.jobs.id"),
           nullable=False),
    Column("automation_id", UUID(as_uuid=True),
           ForeignKey("automation.automation.id"),
           nullable=False),
    schema="analysis",
)

analysis_plans = Table(
    "analysis_plans",
    metadata,
    Column("job_id", UUID(as_uuid=True),
           ForeignKey("jobs.jobs.id"),
           primary_key=True),
    Column("analysis_overview", String, nullable=False),
    Column("analysis_plan", String, nullable=False),
    schema="analysis",
)