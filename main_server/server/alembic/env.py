import asyncio
from logging.config import fileConfig

from sqlalchemy import pool
from sqlalchemy.engine import Connection
from sqlalchemy.ext.asyncio import async_engine_from_config

# Import all models to ensure they register with metadata
from synesis_api.auth.models import users, user_api_keys
from synesis_api.modules.data_sources.models import (
    data_source, file_data_source
)
from synesis_api.modules.data_objects.models import (
    dataset, data_object, object_group, tabular, tabular_group, time_series, time_series_group
)
from synesis_api.modules.pipeline.models import (
    pipeline, pipeline_implementation, pipeline_run
)
from synesis_api.modules.model.models import (
    model, model_implementation, model_instantiated, model_function
)
from synesis_api.modules.analysis.models import (
    analysis, analysis_section, analysis_cell, markdown_cell, code_cell, code_output,
    result_image, result_echart, result_table
)
from synesis_api.modules.entity_graph.models import (
    entity_node, node_group, node_in_group,
    dataset_from_data_source,
    data_source_supported_in_pipeline, dataset_supported_in_pipeline, model_instantiated_supported_in_pipeline,
    dataset_in_pipeline_run, data_source_in_pipeline_run, model_instantiated_in_pipeline_run,
    pipeline_run_output_dataset, pipeline_run_output_model_entity, pipeline_run_output_data_source,
    dataset_in_analysis, data_source_in_analysis, model_instantiated_in_analysis,
)
from synesis_api.modules.visualization.models import (
    image, echart, table
)
from synesis_api.modules.waitlist.models import waitlist
from synesis_api.modules.project.models import project
from synesis_api.modules.kvasir_v1.models import (
    run, run_message, user_message, pydantic_ai_message,
    results_queue, deps, result, analysis_run, swe_run
)
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
    dataset,
    data_object,
    object_group,
    tabular,
    tabular_group,
    time_series,
    time_series_group,
    entity_node,
    node_group,
    node_in_group,
    dataset_from_data_source,
    analysis,
    analysis_section,
    analysis_cell,
    markdown_cell,
    code_cell,
    code_output,
    result_image,
    result_echart,
    result_table,
    dataset_in_analysis,
    data_source_in_analysis,
    model_instantiated_in_analysis,
    pipeline,
    pipeline_implementation,
    data_source_supported_in_pipeline,
    dataset_supported_in_pipeline,
    model_instantiated_supported_in_pipeline,
    pipeline_run,
    dataset_in_pipeline_run,
    data_source_in_pipeline_run,
    model_instantiated_in_pipeline_run,
    pipeline_run_output_dataset,
    pipeline_run_output_model_entity,
    pipeline_run_output_data_source,
    model,
    model_implementation,
    model_instantiated,
    model_function,
    image,
    echart,
    table,
    waitlist,
    project,
    run,
    run_message,
    user_message,
    pydantic_ai_message,
    results_queue,
    deps,
    result,
    analysis_run,
    swe_run,
]

# add your model's MetaData object here
# for 'autogenerate' support
# from myapp import mymodel
# target_metadata = mymodel.Base.metadata
target_metadata = metadata


def include_name(name, type_, parent_names):
    if type_ == "schema":
        return name in ["public", "auth", "data_sources", "data_objects", "analysis", "pipeline", "model", "entity_graph", "visualization", "project", "kvasir_v1", "waitlist"]
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
