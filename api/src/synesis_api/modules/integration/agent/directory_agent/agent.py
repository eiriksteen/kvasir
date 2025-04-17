import json
import redis
import pandas as pd
from pathlib import Path
from dataclasses import dataclass
from pydantic_ai import Agent, RunContext, ModelRetry
from pydantic_ai.settings import ModelSettings
from pydantic_ai.providers.openai import OpenAIProvider
from pydantic_ai.models.openai import OpenAIModel
from .prompt import DIRECTORY_INTEGRATION_SYSTEM_PROMPT
from .schema import IntegrationAgentTimeSeriesOutput
from ..tools import get_target_structure, execute_python_code
from ...schema import DataSubmissionResponse
from .....utils import run_code_in_container, copy_to_container, extract_json_from_markdown, remove_from_container, get_basic_df_info
from .....secrets import OPENAI_API_KEY, OPENAI_API_MODEL


provider = OpenAIProvider(api_key=OPENAI_API_KEY)


model = OpenAIModel(
    model_name=OPENAI_API_MODEL,
    provider=provider
)


directory_integration_agent = Agent(
    model,
    # Currently only time series is supported
    result_type=IntegrationAgentTimeSeriesOutput,
    model_settings=ModelSettings(temperature=0),
    tools=[
        get_target_structure,
        execute_python_code
    ],
    retries=3
)


@dataclass
class DirectoryIntegrationDeps:
    data_directory: Path
    data_description: str
    api_key: str
    redis_stream: redis.Redis


@directory_integration_agent.system_prompt
async def get_system_prompt(ctx: RunContext[DirectoryIntegrationDeps]) -> str:
    _, err = await copy_to_container(ctx.deps.data_directory, target_dir="/tmp")

    if err:
        raise ValueError(f"Error copying file to container: {err}")

    sys_prompt = (
        f"{DIRECTORY_INTEGRATION_SYSTEM_PROMPT}\n\n"
        f"The data to integrate is located at: /tmp/{ctx.deps.data_directory.name}\n\n"
        f"The data description is: {ctx.deps.data_description}"
    )

    return sys_prompt


@directory_integration_agent.tool
async def list_directory_contents(ctx: RunContext[DirectoryIntegrationDeps]):
    """
    Get the structure of the directory.
    """

    await ctx.deps.redis_stream.xadd(str(ctx.job_id), {"agent_message": "Taking a look at the directory contents..."})

    all_paths = ctx.deps.data_directory.glob("**/*")
    visible_paths = [p for p in all_paths if not any(
        part.startswith(".") for part in p.parts)]
    relative_paths = [str(p.relative_to(ctx.deps.data_directory))
                      for p in visible_paths]

    return "\n".join(relative_paths)


@directory_integration_agent.tool
async def get_csv_contents(ctx: RunContext[DirectoryIntegrationDeps], file_path: str):
    """
    Get the contents of a csv file. 
    """

    await ctx.deps.redis_stream.xadd(str(ctx.job_id), {"agent_message": f"Reading {file_path}..."})

    if Path(file_path).suffix != ".csv":
        raise ModelRetry("The file must be a csv file.")

    df = pd.read_csv(ctx.deps.data_directory / Path(file_path))

    return get_basic_df_info(df)


@directory_integration_agent.tool
async def get_json_contents(ctx: RunContext[DirectoryIntegrationDeps], file_path: str):
    """
    Get the contents of a json file. 
    """

    await ctx.deps.redis_stream.xadd(str(ctx.job_id), {"agent_message": f"Reading {file_path}..."})

    if Path(file_path).suffix != ".json":
        raise ModelRetry("The file must be a json file.")

    with open(ctx.deps.data_directory / Path(file_path), "r") as f:
        data = json.load(f)

    return data


@directory_integration_agent.tool
async def get_excel_contents(ctx: RunContext[DirectoryIntegrationDeps], file_path: str):
    """
    Get the contents of an xlsx file, including all sheet names and their contents.
    Returns a dictionary with sheet names as keys and basic info as values.
    """

    await ctx.deps.redis_stream.xadd(str(ctx.job_id), {"agent_message": f"Reading {file_path}..."})

    if Path(file_path).suffix != ".xlsx":
        raise ModelRetry("The file must be an xlsx file.")

    excel_file = pd.ExcelFile(ctx.deps.data_directory / Path(file_path))
    result = {}

    for sheet_name in excel_file.sheet_names:
        df = pd.read_excel(excel_file, sheet_name=sheet_name)
        result[sheet_name] = get_basic_df_info(df)

    return result


@directory_integration_agent.result_validator
async def validate_restructuring(ctx: RunContext[str], result: IntegrationAgentTimeSeriesOutput) -> IntegrationAgentTimeSeriesOutput:
    """
    Submit the restructured data to the database.

    Args:
        ctx: The run context.
        result: The result of the integration agent.
    """

    if not "miya_data" in result.python_code:
        raise ModelRetry(
            "The variable 'miya_data' must be defined in the python code.")

    if not "set_index" in result.python_code:
        raise ModelRetry(
            "Index for the data must be set in the python code, no set_index call found.")

    # We let the LLM submit the data generated in its code to our API
    # This lets us avoid running the LLM-generated code outside of the container, and still get the data output
    submission_code = (
        f"{result.python_code}\n" +
        "from sandbox.integration_tools import submit_restructured_data\n" +
        "print(submit_restructured_data(" +
        f"miya_data.reset_index(), " +
        f"miya_metadata.reset_index(), " +
        f"miya_mapping, " +
        f"data_modality='{result.data_modality}', " +
        f'data_description="""{result.data_description}""", ' +
        f"dataset_name='{result.dataset_name}', " +
        f"index_first_level='{result.index_first_level}', " +
        f"index_second_level='{result.index_second_level}', " +
        f"api_key='{ctx.deps.api_key}'))"
    )

    out, err = await run_code_in_container(submission_code)

    if err:
        raise ModelRetry(f"Error submitting data: {err}")

    api_response = DataSubmissionResponse(
        **extract_json_from_markdown(out)
    )

    result.dataset_id = api_response.dataset_id

    def remove_path(path: Path):
        if path.is_file():
            path.unlink()
        elif path.is_dir():
            for child in path.iterdir():
                remove_path(child)
            path.rmdir()

    remove_path(ctx.deps.data_directory)
    _, err = await remove_from_container(f"/tmp/{ctx.deps.data_directory.name}")
    if err:
        raise RuntimeError(f"Error removing data directory: {err}")

    return result
