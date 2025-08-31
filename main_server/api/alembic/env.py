import asyncio
from logging.config import fileConfig

from sqlalchemy import pool
from sqlalchemy.engine import Connection
from sqlalchemy.ext.asyncio import async_engine_from_config

# Import all models to ensure they register with metadata
from synesis_api.auth.models import users, user_api_keys
from synesis_api.modules.data_sources.models import (
    data_source, file_data_source, tabular_file_data_source,
    data_source_group, data_source_in_group, subgroup,
    feature_in_tabular_file
)
from synesis_api.modules.runs.models import (
    run, run_message, run_pydantic_message,
    data_integration_run_input, data_integration_run_result,
    model_integration_run_input, model_integration_run_result,
    data_source_in_run
)
from synesis_api.modules.data_objects.models import (
    dataset, data_object, object_group, derived_object_source,
    feature, feature_in_group, time_series, time_series_aggregation,
    time_series_aggregation_input
)
from synesis_api.modules.orchestrator.models import (
    chat_message, chat_pydantic_message, conversation,
    chat_context, dataset_context, pipeline_context, analysis_context,
    data_source_context
)
from synesis_api.modules.pipeline.models import (
    pipeline, function, function_input, function_output, function_in_pipeline,
    modality, task, source,
    programming_language, programming_language_version, model, model_task
)
from synesis_api.modules.analysis.models import analysis_jobs_results, analysis_jobs_datasets, analysis_jobs_pipelines, analysis_status_messages
from synesis_api.modules.project.models import project, project_dataset, project_analysis, project_pipeline, project_data_source
from synesis_api.modules.node.models import node, dataset_node, analysis_node, pipeline_node
from synesis_api.app_secrets import DATABASE_URL
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
    tabular_file_data_source,
    run,
    run_message,
    run_pydantic_message,
    data_integration_run_input,
    data_integration_run_result,
    model_integration_run_input,
    model_integration_run_result,
    data_source_in_run,
    data_source_group,
    data_source_in_group,
    subgroup,
    feature_in_tabular_file,
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
    analysis_jobs_pipelines,
    analysis_status_messages,
    chat_message,
    chat_pydantic_message,
    conversation,
    chat_context,
    dataset_context,
    pipeline_context,
    analysis_context,
    data_source_context,
    pipeline,
    function,
    function_input,
    function_output,
    function_in_pipeline,

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
    project_pipeline,
    project_data_source,
    node,
    dataset_node,
    analysis_node,
    pipeline_node,
]

# add your model's MetaData object here
# for 'autogenerate' support
# from myapp import mymodel
# target_metadata = mymodel.Base.metadata
target_metadata = metadata


def include_name(name, type_, parent_names):
    if type_ == "schema":
        return name in ["public", "auth", "data_sources", "runs", "data_objects", "analysis", "orchestrator", "pipeline", "project", "node"]
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

    Calls to context.execute() here emit the given string to the script output.

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
