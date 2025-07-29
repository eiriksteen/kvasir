import asyncio
from logging.config import fileConfig

from sqlalchemy import pool
from sqlalchemy.engine import Connection
from sqlalchemy.ext.asyncio import async_engine_from_config

# Import all models to ensure they register with metadata
from synesis_api.auth.models import users, user_api_keys
from synesis_api.modules.data_integration.models import (
    data_source, file_data_source,
    data_integration_job_input, data_source_in_integration_job, data_integration_job_result,
    data_source_group, data_source_in_group, subgroup
)
from synesis_api.modules.jobs.models import job
from synesis_api.modules.data_objects.models import (
    dataset, data_object, object_group, derived_object_source,
    feature, feature_in_group, time_series, time_series_aggregation,
    time_series_aggregation_input
)
from synesis_api.modules.chat.models import (
    chat_message, pydantic_message, conversation, conversation_mode,
    context, dataset_context, automation_context, analysis_context
)
from synesis_api.modules.automation.models import (
    automation, function, function_input_structure, function_output_structure,
    data_object_computed_from_function, modality, task, source,
    programming_language, programming_language_version, model, model_task
)
from synesis_api.modules.analysis.models import analysis_jobs_results, analysis_jobs_datasets, analysis_jobs_automations, analysis_status_messages
from synesis_api.modules.project.models import project, project_dataset, project_analysis, project_automation, project_data_source
from synesis_api.modules.node.models import node, dataset_node, analysis_node, automation_node
from synesis_api.modules.model_integration.models import model_integration_job_result, model_integration_job_input
from synesis_api.secrets import DATABASE_URL
from synesis_api.database.core import metadata

from alembic import context

# this is the Alembic Config object, which provides
# access to the values within the .ini file in use.
config = context.config

# Interpret the config file for Python logging.
# This line sets up loggers basically.
if config.config_file_name is not None:
    fileConfig(config.config_file_name)

# Explicitly reference all models to ensure they are included in the metadata
__all__ = [
    users,
    user_api_keys,
    data_source,
    file_data_source,
    data_integration_job_input,
    data_source_in_integration_job,
    data_integration_job_result,
    data_source_group,
    data_source_in_group,
    subgroup,
    job,
    dataset,
    data_object,
    object_group,
    derived_object_source,
    feature,
    feature_in_group,
    time_series,
    time_series_aggregation,
    time_series_aggregation_input,
    analysis_jobs_results,
    analysis_jobs_datasets,
    analysis_jobs_automations,
    analysis_status_messages,
    chat_message,
    pydantic_message,
    conversation,
    conversation_mode,
    context,
    dataset_context,
    automation_context,
    analysis_context,
    automation,
    function,
    function_input_structure,
    function_output_structure,
    data_object_computed_from_function,
    modality,
    task,
    source,
    programming_language,
    programming_language_version,
    model,
    model_task,
    project,
    project_dataset,
    project_analysis,
    project_automation,
    project_data_source,
    node,
    dataset_node,
    analysis_node,
    automation_node,
    model_integration_job_result,
    model_integration_job_input
]

# add your model's MetaData object here
# for 'autogenerate' support
# from myapp import mymodel
# target_metadata = mymodel.Base.metadata
target_metadata = metadata


def include_name(name, type_, parent_names):
    if type_ == "schema":
        return name in ["public", "auth", "data_integration", "jobs", "data_objects", "analysis", "chat", "automation", "project", "node", "model_integration"]
    else:
        return True

# other values from the config, defined by the needs of env.py,
# can be acquired:
# my_important_option = config.get_main_option("my_important_option")
# ... etc.


config.set_main_option("sqlalchemy.url", DATABASE_URL)


def run_migrations_offline() -> None:
    """Run migrations in 'offline' mode.

    This configures the context with just a URL
    and not an Engine, though an Engine is acceptable
    here as well.  By skipping the Engine creation
    we don't even need a DBAPI to be available.

    Calls to context.execute() here emit the given string to the
    script output.

    """
    url = config.get_main_option("sqlalchemy.url")
    context.configure(
        url=url,
        target_metadata=target_metadata,
        literal_binds=True,
        dialect_opts={"paramstyle": "named"},
        include_schemas=True,
        include_name=include_name
    )

    with context.begin_transaction():
        context.run_migrations()


def do_run_migrations(connection: Connection) -> None:
    context.configure(
        connection=connection,
        target_metadata=target_metadata,
        include_schemas=True,
        include_name=include_name
    )

    with context.begin_transaction():
        context.run_migrations()


async def run_async_migrations() -> None:
    """In this scenario we need to create an Engine
    and associate a connection with the context.

    """

    connectable = async_engine_from_config(
        config.get_section(config.config_ini_section, {}),
        prefix="sqlalchemy.",
        poolclass=pool.NullPool,
    )

    async with connectable.connect() as connection:
        await connection.run_sync(do_run_migrations)

    await connectable.dispose()


def run_migrations_online() -> None:
    """Run migrations in 'online' mode."""

    asyncio.run(run_async_migrations())


if context.is_offline_mode():
    run_migrations_offline()
else:
    run_migrations_online()
