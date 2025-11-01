import json
from uuid import UUID
from pydantic_ai import RunContext, ModelRetry, FunctionToolset


from project_server.agents.extraction.deps import ExtractionDeps
from project_server.utils.code_utils import run_python_code_in_container
from synesis_schemas.main_server import (
    Dataset,
    DataSource,
    Function,
    ModelImplementation,
    ModelEntityInDB,
    ObjectGroup,
    DatasetCreate,
    DataObjectGroupCreate,
    FunctionCreate,
    FunctionUpdateCreate,
    ModelImplementationCreate,
    ModelUpdateCreate,
    ModelEntityImplementationCreate,
    DataSourceCreate,
    DataObjectCreate,
    PipelineImplementationCreate,
    PipelineImplementationInDB,
)


# data sources

async def submit_data_source(ctx: RunContext[ExtractionDeps], python_code: str, variable_name: str) -> DataSource:
    """Submit a data source with type-specific fields to the system."""
    try:
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
        if err:
            raise ValueError(f"Code execution error: {err}")

        result_data = json.loads(out.strip())
        return DataSource(**result_data)
    except Exception as e:
        raise ModelRetry(
            f"Failed to submit data source from code: {str(e)}")


# datasets


async def submit_dataset(ctx: RunContext[ExtractionDeps], python_code: str, variable_name: str) -> Dataset:
    try:
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
        if err:
            raise ValueError(f"Code execution error: {err}")

        result_data = json.loads(out.strip())
        return Dataset(**result_data)
    except Exception as e:
        raise ModelRetry(f"Failed to submit dataset from code: {str(e)}")


async def submit_object_group(
        ctx: RunContext[ExtractionDeps],
        dataset_id: UUID,
        python_code: str,
        variable_name: str) -> ObjectGroup:
    try:
        submission_code = (
            f"{python_code}\n"
            "import asyncio\n"
            "from project_server.client import ProjectClient\n"
            "from project_server.client.requests.data_objects import post_object_group\n"
            "from synesis_schemas.main_server import DataObjectGroupCreate\n"
            "from uuid import UUID\n"
            "import json\n"
            "\n"
            "async def run_submission():\n"
            f"    client = ProjectClient(bearer_token='{ctx.deps.bearer_token}')\n"
            f"    dataset_id = UUID('{dataset_id}')\n"
            f"    group_create = DataObjectGroupCreate(**{variable_name})\n"
            "    # The agent should have prepared 'files' list with FileInput objects\n"
            "    if 'files' not in locals() and 'files' not in globals():\n"
            "        raise ValueError('files variable not found. The agent must create FileInput objects for each dataframe in objects_files.')\n"
            f"    result = await post_object_group(client, dataset_id, group_create, files)\n"
            "    print(json.dumps(result.model_dump(), default=str))\n"
            "\n"
            "asyncio.run(run_submission())"
        )
        out, err = await run_python_code_in_container(submission_code, ctx.deps.container_name)
        if err:
            raise ValueError(f"Code execution error: {err}")

        result_data = json.loads(out.strip())
        return ObjectGroup(**result_data)
    except Exception as e:
        raise ModelRetry(
            f"Failed to submit object group from code: {str(e)}")

# TODO: More modalities


# functions

async def submit_function(ctx: RunContext[ExtractionDeps], python_code: str, variable_name: str) -> Function:
    try:
        submission_code = (
            f"{python_code}\n"
            "import asyncio\n"
            "from project_server.client import ProjectClient\n"
            "from project_server.client.requests.function import post_function\n"
            "from synesis_schemas.main_server import FunctionCreate\n"
            "import json\n"
            "\n"
            "async def run_submission():\n"
            f"    client = ProjectClient(bearer_token='{ctx.deps.bearer_token}')\n"
            f"    function_data = FunctionCreate(**{variable_name})\n"
            f"    result = await post_function(client, function_data)\n"
            "    print(json.dumps(result.model_dump(), default=str))\n"
            "\n"
            "asyncio.run(run_submission())"
        )
        out, err = await run_python_code_in_container(submission_code, ctx.deps.container_name)
        if err:
            raise ValueError(f"Code execution error: {err}")

        result_data = json.loads(out.strip())
        return Function(**result_data)
    except Exception as e:
        raise ModelRetry(f"Failed to submit function from code: {str(e)}")


async def submit_function_update(ctx: RunContext[ExtractionDeps], python_code: str, variable_name: str) -> Function:
    try:
        submission_code = (
            f"{python_code}\n"
            "import asyncio\n"
            "from project_server.client import ProjectClient\n"
            "from project_server.client.requests.function import post_update_function\n"
            "from synesis_schemas.main_server import FunctionUpdateCreate\n"
            "import json\n"
            "\n"
            "async def run_submission():\n"
            f"    client = ProjectClient(bearer_token='{ctx.deps.bearer_token}')\n"
            f"    function_data = FunctionUpdateCreate(**{variable_name})\n"
            f"    result = await post_update_function(client, function_data)\n"
            "    print(json.dumps(result.model_dump(), default=str))\n"
            "\n"
            "asyncio.run(run_submission())"
        )
        out, err = await run_python_code_in_container(submission_code, ctx.deps.container_name)
        if err:
            raise ValueError(f"Code execution error: {err}")

        result_data = json.loads(out.strip())
        return Function(**result_data)
    except Exception as e:
        raise ModelRetry(
            f"Failed to submit function update from code: {str(e)}")


# models


async def submit_model(ctx: RunContext[ExtractionDeps], python_code: str, variable_name: str) -> ModelImplementation:
    """
    A model refers to the code defining a model. It can be instantiated to create a model entity.
    """
    try:
        submission_code = (
            f"{python_code}\n"
            "import asyncio\n"
            "from project_server.client import ProjectClient\n"
            "from project_server.client.requests.model import post_model\n"
            "from synesis_schemas.main_server import ModelImplementationCreate\n"
            "import json\n"
            "\n"
            "async def run_submission():\n"
            f"    client = ProjectClient(bearer_token='{ctx.deps.bearer_token}')\n"
            f"    model_data = ModelImplementationCreate(**{variable_name})\n"
            f"    result = await post_model(client, model_data)\n"
            "    print(json.dumps(result.model_dump(), default=str))\n"
            "\n"
            "asyncio.run(run_submission())"
        )
        out, err = await run_python_code_in_container(submission_code, ctx.deps.container_name)
        if err:
            raise ValueError(f"Code execution error: {err}")

        result_data = json.loads(out.strip())
        return ModelImplementation(**result_data)
    except Exception as e:
        raise ModelRetry(f"Failed to submit model from code: {str(e)}")


async def submit_model_update(ctx: RunContext[ExtractionDeps], python_code: str, variable_name: str) -> ModelImplementation:
    try:
        submission_code = (
            f"{python_code}\n"
            "import asyncio\n"
            "from project_server.client import ProjectClient\n"
            "from project_server.client.requests.model import post_update_model\n"
            "from synesis_schemas.main_server import ModelUpdateCreate\n"
            "import json\n"
            "\n"
            "async def run_submission():\n"
            f"    client = ProjectClient(bearer_token='{ctx.deps.bearer_token}')\n"
            f"    request = ModelUpdateCreate(**{variable_name})\n"
            f"    result = await post_update_model(client, request)\n"
            "    print(json.dumps(result.model_dump(), default=str))\n"
            "\n"
            "asyncio.run(run_submission())"
        )
        out, err = await run_python_code_in_container(submission_code, ctx.deps.container_name)
        if err:
            raise ValueError(f"Code execution error: {err}")

        result_data = json.loads(out.strip())
        return ModelImplementation(**result_data)
    except Exception as e:
        raise ModelRetry(f"Failed to submit model update from code: {str(e)}")


async def submit_model_entity(ctx: RunContext[ExtractionDeps], python_code: str, variable_name: str) -> ModelEntityInDB:
    """
    A model entity refers to an instantiated model that is configured and often including weights.
    """
    try:
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
        if err:
            raise ValueError(f"Code execution error: {err}")

        result_data = json.loads(out.strip())
        return ModelEntityInDB(**result_data)
    except Exception as e:
        raise ModelRetry(f"Failed to submit model entity from code: {str(e)}")


# pipelines


async def submit_pipeline_implementation(ctx: RunContext[ExtractionDeps], python_code: str, variable_name: str) -> PipelineImplementationInDB:
    """
    Create a new pipeline implementation that defines the execution logic for a pipeline.

    Note: If the user wants to associate this implementation with a specific existing pipeline,
    remember to include the pipeline_id in the PipelineImplementationCreate data. Otherwise,
    you can include pipeline_create to create a new pipeline along with the implementation.
    """
    try:
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
            f"    # Add pipeline to project\n"
            f"    add_entity_request = AddEntityToProject(\n"
            f"        project_id=UUID('{ctx.deps.project.id}'),\n"
            f"        entity_type='pipeline',\n"
            f"        entity_id=result.id\n"
            f"    )\n"
            f"    await post_add_entity(client, add_entity_request)\n"
            "    print(json.dumps(result.model_dump(), default=str))\n"
            "\n"
            "asyncio.run(run_submission())"
        )
        out, err = await run_python_code_in_container(submission_code, ctx.deps.container_name)
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
        submit_object_group,
        submit_function,
        submit_pipeline_implementation,
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
        f"{schema_str}\n\n"
        "Note: Requires file uploads - the agent must create FileInput objects for dataframes in all groups. "
        f"The dataframes must abide by the following data object create schema:\n\n{json.dumps(data_objects_schema, indent=2)}\n\n"
        "FileInput objects should have: field_name (str), filename (str), file_data (bytes), content_type (str). "
    )


def get_object_group_schema() -> str:
    schema_str = json.dumps(
        DataObjectGroupCreate.model_json_schema(), indent=2)
    data_objects_schema = DataObjectCreate.model_json_schema()
    return (
        f"{schema_str}\n\n"
        "Note: Requires file uploads - the agent must create FileInput objects for each dataframe in objects_files. "
        f"The dataframes must abide by the following data object create schema:\n\n{json.dumps(data_objects_schema, indent=2)}\n\n"
        "FileInput objects should have: field_name (str), filename (str), file_data (bytes), content_type (str). "
    )


def get_function_schema() -> str:
    return json.dumps(FunctionCreate.model_json_schema(), indent=2)


def get_function_update_schema() -> str:
    return json.dumps(FunctionUpdateCreate.model_json_schema(), indent=2)


def get_model_schema() -> str:
    return json.dumps(ModelImplementationCreate.model_json_schema(), indent=2)


def get_model_update_schema() -> str:
    return json.dumps(ModelUpdateCreate.model_json_schema(), indent=2)


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
        get_object_group_schema,
        get_function_schema,
        get_pipeline_implementation_schema,
    ],
    max_retries=3
)
