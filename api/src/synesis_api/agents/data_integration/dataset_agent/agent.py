import json
import uuid
import pandas as pd
from typing import List
from pathlib import Path
from dataclasses import dataclass
from pydantic_ai import Agent, RunContext, ModelRetry
from pydantic_ai.settings import ModelSettings
from synesis_api.agents.data_integration.dataset_agent.prompt import DATASET_INTEGRATION_SYSTEM_PROMPT
from synesis_api.agents.data_integration.shared_tools import (
    execute_python_code,
    get_csv_contents,
    get_json_contents,
    get_excel_contents
)
from synesis_api.agents.data_integration.dataset_agent.utils import list_directory_contents, resolve_path_from_directory_name
from synesis_api.utils import (
    copy_file_or_directory_to_container,
    get_basic_df_info,
    get_model,
    run_python_function_in_container
)
from synesis_data_structures.time_series.definitions import get_data_structures_overview, get_data_structure_description
from synesis_api.base_schema import BaseSchema


@dataclass
class DatasetAgentDeps:
    job_id: uuid.UUID
    data_description: str
    data_directories: List[Path]
    api_key: str


class DatasetAgentOutput(BaseSchema):
    data_directories: List[Path]
    summary: str
    code_explanation: str
    code: str


class DatasetAgentOutputWithDatasetId(DatasetAgentOutput):
    dataset_id: uuid.UUID


model = get_model()


dataset_integration_agent = Agent(
    model,
    output_type=DatasetAgentOutput,
    model_settings=ModelSettings(temperature=0),
    tools=[
        execute_python_code,
        get_csv_contents,
        get_json_contents,
        get_excel_contents,
        get_data_structures_overview,
        get_data_structure_description
    ],
    retries=3
)


@dataset_integration_agent.system_prompt
async def get_system_prompt(ctx: RunContext[DatasetAgentDeps]) -> str:

    for data_directory in ctx.deps.data_directories:
        _, err = await copy_file_or_directory_to_container(data_directory, target_dir="/tmp")

    if err:
        raise ValueError(f"Error copying file to container: {err}")

    sys_prompt = (
        f"{DATASET_INTEGRATION_SYSTEM_PROMPT}\n\n"
        f"The data description is: {ctx.deps.data_description}"
        "Content of the directories to integrate from:\n\n"
        "\n\n".join(
            [f"Directory name: {data_directory.name}\nContents: {list_directory_contents(data_directory)}" for data_directory in ctx.deps.data_directories])
    )

    return sys_prompt


@dataset_integration_agent.output_validator
async def validate_data_integration(
        _: RunContext[DatasetAgentDeps],
        result: DatasetAgentOutput
) -> DatasetAgentOutputWithDatasetId:
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

    return DatasetAgentOutputWithDatasetId(
        **result.model_dump(),
        dataset_id=output_obj["id"]
    )
