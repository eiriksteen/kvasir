import json
import uuid
import pandas as pd
from pathlib import Path
from dataclasses import dataclass
from typing import List
from pydantic_ai import Agent, RunContext, ModelRetry
from pydantic_ai.settings import ModelSettings
from synesis_api.agents.data_integration.local_agent.prompt import LOCAL_INTEGRATION_SYSTEM_PROMPT
from synesis_api.agents.data_integration.shared_tools import execute_python_code
from synesis_api.agents.data_integration.local_agent.utils import list_directory_contents, resolve_path_from_directory_name
from synesis_api.utils import (
    copy_file_or_directory_to_container,
    get_basic_df_info,
    get_model,
    run_python_function_in_container
)
from synesis_data_structures.time_series.definitions import get_data_structures_overview, get_data_structure_description
from synesis_api.base_schema import BaseSchema


@dataclass
class IntegrationAgentDeps:
    job_id: uuid.UUID
    data_description: str
    data_directories: List[Path]
    api_key: str


class IntegrationAgentOutput(BaseSchema):
    data_directories: List[Path]
    summary: str
    code_explanation: str
    code: str


class IntegrationAgentOutputWithDatasetId(IntegrationAgentOutput):
    dataset_id: uuid.UUID


model = get_model()


local_integration_agent = Agent(
    model,
    output_type=IntegrationAgentOutput,
    model_settings=ModelSettings(temperature=0),
    tools=[
        execute_python_code,
        get_data_structures_overview,
        get_data_structure_description
    ],
    retries=3
)


@local_integration_agent.system_prompt
async def get_system_prompt(ctx: RunContext[IntegrationAgentDeps]) -> str:

    for data_directory in ctx.deps.data_directories:
        _, err = await copy_file_or_directory_to_container(data_directory, target_dir="/tmp")

    if err:
        raise ValueError(f"Error copying file to container: {err}")

    sys_prompt = (
        f"{LOCAL_INTEGRATION_SYSTEM_PROMPT}\n\n"
        f"The data description is: {ctx.deps.data_description}"
        "Content of the directories to integrate from:\n\n"
        "\n\n".join(
            [f"Directory name: {data_directory.name}\nContents: {list_directory_contents(data_directory)}" for data_directory in ctx.deps.data_directories])
    )

    return sys_prompt


@local_integration_agent.tool_plain
async def get_csv_contents(data_directory: str, file_name: str):
    """
    Get the contents of a csv file. 

    Args:
        ctx: The context
        file_path: The path to the csv file
    """

    if Path(file_name).suffix != ".csv":
        raise ModelRetry("The file must be a csv file.")

    # TODO: Fix since is not robust (duplicate directory names not supported)
    # Will be fixed with new structure to run agent functions behind MCP
    path = resolve_path_from_directory_name(data_directory, Path("/tmp"))

    df = pd.read_csv(path / file_name)

    return get_basic_df_info(df)


@local_integration_agent.tool_plain
async def get_json_contents(data_directory: str, file_name: str):
    """
    Get the contents of a json file. 

    Args:
        ctx: The context
        file_path: The path to the json file
    """

    if Path(file_name).suffix != ".json":
        raise ModelRetry("The file must be a json file.")

    path = resolve_path_from_directory_name(data_directory, Path("/tmp"))

    with open(path / file_name, "r") as f:
        data = json.load(f)

    return data


@local_integration_agent.tool_plain
async def get_excel_contents(data_directory: str, file_name: str):
    """
    Get the contents of an xlsx file, including all sheet names and their contents.
    Returns a dictionary with sheet names as keys and basic info as values.

    Args:
        ctx: The context
        file_path: The path to the xlsx file
    """

    if Path(file_name).suffix != ".xlsx":
        raise ModelRetry("The file must be an xlsx file.")

    path = resolve_path_from_directory_name(data_directory, Path("/tmp"))

    excel_file = pd.ExcelFile(path / file_name)
    result = {}

    for sheet_name in excel_file.sheet_names:
        df = pd.read_excel(excel_file, sheet_name=sheet_name)
        result[sheet_name] = get_basic_df_info(df)

    return result


@local_integration_agent.output_validator
async def validate_data_integration(
        _: RunContext[IntegrationAgentDeps],
        result: IntegrationAgentOutput
) -> IntegrationAgentOutputWithDatasetId:
    """
    Submit the restructured data to the database.

    Args:
        _: The context.
        result: The result of the integration agent.
    """

    out, err = await run_python_function_in_container(
        base_script=result.code,
        function_name="submit_dataset_to_api",
        input_variables=["dataset_dict"],
        source_module="sandbox.tools",
        print_output=True
    )

    if err:
        raise ModelRetry(f"Error submitting dataset to API: {err}")

    output_obj = json.loads(out)

    return IntegrationAgentOutputWithDatasetId(
        **result.model_dump(),
        dataset_id=output_obj["id"]
    )
