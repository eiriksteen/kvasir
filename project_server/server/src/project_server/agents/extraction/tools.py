import json
from uuid import UUID
from typing import Optional
from pydantic_ai import RunContext, ModelRetry, FunctionToolset


from project_server.agents.extraction.deps import ExtractionDeps
from project_server.utils.code_utils import run_python_code_in_container, remove_print_statements_from_code
from synesis_schemas.main_server import (
    Dataset,
    DataSource,
    ModelImplementation,
    ModelEntityInDB,
    DatasetCreate,
    ModelUpdateCreate,
    ModelEntityImplementationCreate,
    DataSourceCreate,
    DataObjectCreate,
    PipelineImplementationCreate,
    PipelineImplementationInDB,
)
from project_server.worker import logger


# data sources

async def submit_data_source(ctx: RunContext[ExtractionDeps], python_code: str, variable_name: str) -> DataSource:
    """Submit a data source with type-specific fields to the system."""
    try:
        python_code = remove_print_statements_from_code(python_code)
        submission_code = (
            f"{python_code}\n"
            "import asyncio\n"
            "from project_server.client import ProjectClient\n"
            "from project_server.client.requests.data_sources import post_data_source\n"
            "from project_server.client.requests.project import post_add_entity\n"
            "from synesis_schemas.main_server import DataSourceCreate, AddEntityToProject\n"
            "from uuid import UUID\n"
            "import json\n"
            "\n"
            "async def run_submission():\n"
            f"    client = ProjectClient(bearer_token='{ctx.deps.bearer_token}')\n"
            f"    request = DataSourceCreate(**{variable_name})\n"
            f"    result = await post_data_source(client, request)\n"
            f"    # Add data source to project\n"
            f"    add_entity_request = AddEntityToProject(\n"
            f"        project_id=UUID('{ctx.deps.project.id}'),\n"
            f"        entity_type='data_source',\n"
            f"        entity_id=result.id\n"
            f"    )\n"
            f"    await post_add_entity(client, add_entity_request)\n"
            "    print(json.dumps(result.model_dump(), default=str))\n"
            "\n"
            "asyncio.run(run_submission())"
        )
        out, err = await run_python_code_in_container(submission_code, ctx.deps.container_name)

        logger.info("@"*100)
        logger.info("SUBMIT DATA SOURCE CODE")
        logger.info(python_code)
        logger.info("OUT")
        logger.info(out)
        logger.info("ERR")
        logger.info(err)

        if err:
            raise ValueError(f"Code execution error: {err}")

        result_data = json.loads(out.strip())
        return DataSource(**result_data)
    except Exception as e:
        raise ModelRetry(
            f"Failed to submit data source from code: {str(e)}")


# datasets


async def submit_dataset(ctx: RunContext[ExtractionDeps], python_code: str, variable_name: str) -> Dataset:
    """"Submit a dataset including upload files with object metadata. All files must be parquet!"""
    try:
        python_code = remove_print_statements_from_code(python_code)
        submission_code = (
            f"{python_code}\n"
            "import asyncio\n"
            "from project_server.client import ProjectClient\n"
            "from project_server.client.requests.data_objects import post_dataset\n"
            "from project_server.client.requests.project import post_add_entity\n"
            "from synesis_schemas.main_server import DatasetCreate, AddEntityToProject\n"
            "from uuid import UUID\n"
            "import json\n"
            "\n"
            "async def run_submission():\n"
            f"    client = ProjectClient(bearer_token='{ctx.deps.bearer_token}')\n"
            f"    dataset_create = DatasetCreate(**{variable_name})\n"
            "    # The agent should have prepared 'files' list with FileInput objects\n"
            "    if 'files' not in locals() and 'files' not in globals():\n"
            "        raise ValueError('files variable not found. The agent must create FileInput objects for dataframes in all groups.')\n"
            f"    result = await post_dataset(client, files, dataset_create)\n"
            f"    # Add dataset to project\n"
            f"    add_entity_request = AddEntityToProject(\n"
            f"        project_id=UUID('{ctx.deps.project.id}'),\n"
            f"        entity_type='dataset',\n"
            f"        entity_id=result.id\n"
            f"    )\n"
            f"    await post_add_entity(client, add_entity_request)\n"
            "    print(json.dumps(result.model_dump(), default=str))\n"
            "\n"
            "asyncio.run(run_submission())"
        )
        out, err = await run_python_code_in_container(submission_code, ctx.deps.container_name)
        logger.info("@"*100)
        logger.info("SUBMIT DATASET CODE")
        logger.info(python_code)
        logger.info("OUT")
        logger.info(out)
        logger.info("ERR")
        logger.info(err)
        if err:
            raise ValueError(f"Code execution error: {err}")

        result_data = json.loads(out.strip())
        return Dataset(**result_data)
    except Exception as e:
        raise ModelRetry(f"Failed to submit dataset from code: {str(e)}")


# TODO: More modalities


async def submit_model_entity(ctx: RunContext[ExtractionDeps], python_code: str, variable_name: str) -> ModelEntityInDB:
    """
    A model entity refers to an instantiated model that is configured and often including weights.
    """
    try:
        python_code = remove_print_statements_from_code(python_code)
        submission_code = (
            f"{python_code}\n"
            "import asyncio\n"
            "from project_server.client import ProjectClient\n"
            "from project_server.client.requests.model import post_model_entity_implementation\n"
            "from project_server.client.requests.project import post_add_entity\n"
            "from synesis_schemas.main_server import ModelEntityImplementationCreate, AddEntityToProject\n"
            "from uuid import UUID\n"
            "import json\n"
            "\n"
            "async def run_submission():\n"
            f"    client = ProjectClient(bearer_token='{ctx.deps.bearer_token}')\n"
            f"    model_entity_impl_data = ModelEntityImplementationCreate(**{variable_name})\n"
            f"    result = await post_model_entity_implementation(client, model_entity_impl_data)\n"
            f"    # Add model entity to project\n"
            f"    add_entity_request = AddEntityToProject(\n"
            f"        project_id=UUID('{ctx.deps.project.id}'),\n"
            f"        entity_type='model_entity',\n"
            f"        entity_id=result.id\n"
            f"    )\n"
            f"    await post_add_entity(client, add_entity_request)\n"
            "    print(json.dumps(result.model_dump(), default=str))\n"
            "\n"
            "asyncio.run(run_submission())"
        )
        out, err = await run_python_code_in_container(submission_code, ctx.deps.container_name)
        logger.info("@"*100)
        logger.info("SUBMIT MODEL ENTITY CODE")
        logger.info(python_code)
        logger.info("OUT")
        logger.info(out)
        logger.info("ERR")
        logger.info(err)
        if err:
            raise ValueError(f"Code execution error: {err}")

        result_data = json.loads(out.strip())
        return ModelEntityInDB(**result_data)
    except Exception as e:
        raise ModelRetry(f"Failed to submit model entity from code: {str(e)}")


# pipelines


async def submit_pipeline_implementation(
    ctx: RunContext[ExtractionDeps],
    python_code: str,
    variable_name: str,
    pipeline_id: Optional[UUID] = None
) -> PipelineImplementationInDB:
    """
    Create a new pipeline implementation that defines the execution logic for a pipeline.

    Note: If the user wants to associate this implementation with a specific existing pipeline,
    remember to include the pipeline_id in the PipelineImplementationCreate data. Otherwise,
    you can include pipeline_create to create a new pipeline along with the implementation.
    """
    try:
        python_code = remove_print_statements_from_code(python_code)
        submission_code = (
            f"{python_code}\n"
            "import asyncio\n"
            "from project_server.client import ProjectClient\n"
            "from project_server.client.requests.pipeline import post_pipeline_implementation\n"
            "from project_server.client.requests.project import post_add_entity\n"
            "from synesis_schemas.main_server import PipelineImplementationCreate, AddEntityToProject\n"
            "from uuid import UUID\n"
            "import json\n"
            "\n"
            "async def run_submission():\n"
            f"    client = ProjectClient(bearer_token='{ctx.deps.bearer_token}')\n"
            f"    pipeline_impl_data = PipelineImplementationCreate(**{variable_name})\n"
            f"    result = await post_pipeline_implementation(client, pipeline_impl_data)\n"
            f"    # Add pipeline to project only if no existing pipeline\n"
            f"    if not {pipeline_id is None}:\n"
            f"        add_entity_request = AddEntityToProject(\n"
            f"            project_id=UUID('{ctx.deps.project.id}'),\n"
            f"            entity_type='pipeline',\n"
            f"            entity_id=result.id\n"
            f"        )\n"
            f"        await post_add_entity(client, add_entity_request)\n"
            "    print(json.dumps(result.model_dump(), default=str))\n"
            "\n"
            "asyncio.run(run_submission())"
        )
        out, err = await run_python_code_in_container(submission_code, ctx.deps.container_name)
        logger.info("@"*100)
        logger.info("SUBMIT PIPELINE IMPLEMENTATION CODE")
        logger.info(python_code)
        logger.info("OUT")
        logger.info(out)
        logger.info("ERR")
        logger.info(err)
        if err:
            raise ValueError(f"Code execution error: {err}")

        result_data = json.loads(out.strip())
        return PipelineImplementationInDB(**result_data)
    except Exception as e:
        raise ModelRetry(
            f"Failed to submit pipeline implementation from code: {str(e)}")


submission_toolset = FunctionToolset[ExtractionDeps](
    tools=[
        submit_data_source,
        submit_dataset,
        submit_pipeline_implementation,
        submit_model_entity
    ],
    max_retries=3
)


# TODO: Add analyses


def get_data_source_schema() -> str:
    return json.dumps(DataSourceCreate.model_json_schema(), indent=2)


def get_dataset_schema() -> str:
    schema_str = json.dumps(DatasetCreate.model_json_schema(), indent=2)
    data_objects_schema = DataObjectCreate.model_json_schema()
    return (
        f"{schema_str}\n\n" +
        "Note: Requires file uploads - the agent must create FileInput objects for dataframes in all groups.\n" +
        f"The dataframes must abide by the following data object create schema:\n\n{json.dumps(data_objects_schema, indent=2)}\n\n" +
        "FileInput objects should have: filename (str), file_data (bytes), content_type (str).\n" +
        "All files must be parquet!"
    )


def get_model_entity_schema() -> str:
    schema_str = json.dumps(
        ModelEntityImplementationCreate.model_json_schema(), indent=2)
    return (
        f"{schema_str}\n\n"
        "Validation rules: Either model_implementation_id or model_implementation_create must be provided. "
        "Either model_entity_id or model_entity_create must be provided."
    )


def get_pipeline_implementation_schema() -> str:
    return json.dumps(PipelineImplementationCreate.model_json_schema(), indent=2)


schema_toolset = FunctionToolset[ExtractionDeps](
    tools=[
        get_data_source_schema,
        get_dataset_schema,
        get_pipeline_implementation_schema,
        get_model_entity_schema,
    ],
    max_retries=3
)
