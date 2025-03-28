import io
import aiofiles
import pandas as pd
from pathlib import Path
from dataclasses import dataclass
from pydantic_ai import Agent, RunContext, ModelRetry
from pydantic_ai.settings import ModelSettings
from pydantic_ai.models.openai import OpenAIModel
from .prompt import INTEGRATION_SYSTEM_PROMPT, TIME_SERIES_TARGET_STRUCTURE
from ..schema import IntegrationAgentOutput, DataSubmissionResponse
from ...utils import get_df_info, run_code_in_container, copy_file_to_container, extract_json_from_markdown
from ...secrets import OPENAI_API_KEY, OPENAI_API_MODEL


model = OpenAIModel(
    model_name=OPENAI_API_MODEL,
    api_key=OPENAI_API_KEY
)


integration_agent = Agent(
    model,
    result_type=IntegrationAgentOutput,
    model_settings=ModelSettings(
        temperature=0.1
    )
)


@dataclass
class IntegrationDeps:
    data_path: Path
    data_description: str
    api_key: str


@integration_agent.system_prompt
async def get_system_prompt(ctx: RunContext[IntegrationDeps]) -> str:
    _, err = await copy_file_to_container(ctx.deps.data_path, target_dir="/tmp")

    if err:
        raise ValueError(f"Error copying file to container: {err}")

    sys_prompt = (
        f"{INTEGRATION_SYSTEM_PROMPT}\n\n"
        f"The data to integrate is located at: /tmp/{ctx.deps.data_path.name}\n\n"
        f"The data description is: {ctx.deps.data_description}"
    )

    return sys_prompt


@integration_agent.tool
async def visualize_raw_data(ctx: RunContext[IntegrationDeps]):
    """
    Visualize basic information about the raw data.
    """
    if not ctx.deps.data_path.exists():
        raise FileNotFoundError(f"File not found: {ctx.deps.data_path}")

    if ctx.deps.data_path.suffix == ".csv":
        async with aiofiles.open(ctx.deps.data_path) as f:
            text = await f.read()

        with io.StringIO(text) as text_io:
            data = pd.read_csv(text_io)

        return get_df_info(data)
    else:
        raise ValueError(
            f"Unsupported file type, currently only csv files are supported.")


@integration_agent.tool_plain
def get_target_structure(data_modality: str):
    """
    Get the target structure of the data.

    Args:
        data_modality: The modality of the data to get the structure for, one of ["time_series", "tabular", "image", "text"]
    """
    assert data_modality in ["time_series", "tabular", "image", "text"]

    if data_modality == "time_series":
        return TIME_SERIES_TARGET_STRUCTURE
    else:
        raise ValueError(
            f"The target structure for {data_modality} data is not yet implemented.")


@integration_agent.tool_plain
async def execute_python_code(python_code: str):
    """
    Execute a python code block.
    """
    out, err = await run_code_in_container(python_code)

    if err:
        raise ModelRetry(f"Error executing code: {err}")

    return out


@integration_agent.result_validator
async def validate_restructuring(ctx: RunContext[str], result: IntegrationAgentOutput) -> IntegrationAgentOutput:
    """
    Submit the restructured data to the database.

    Args:
        ctx: The run context.
        result: The result of the integration agent.
    """

    if not "restructured_data" in result.python_code:
        raise ModelRetry(
            "The variable 'restructured_data' must be defined in the python code.")

    # We let the LLM submit the data generated in its code to our API
    # This lets us avoid running the LLM-generated code outside of the container, and still get the data output
    submission_code = (
        f"{result.python_code}\n" +
        "from sandbox.integration_tools import submit_restructured_data\n" +
        "print(submit_restructured_data(" +
        f"restructured_data, data_modality='{result.data_modality}', " +
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

    return result
