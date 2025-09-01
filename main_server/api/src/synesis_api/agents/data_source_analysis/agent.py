from pathlib import Path
from pydantic_ai import Agent, ModelRetry, RunContext
from pydantic_ai.settings import ModelSettings

from synesis_api.agents.data_source_analysis.deps import DataSourceAnalysisAgentDeps
from synesis_api.agents.data_source_analysis.prompt import DATA_SOURCE_AGENT_SYSTEM_PROMPT
from synesis_api.agents.shared_tools import (
    execute_python_code,
    get_csv_contents,
    get_json_contents,
    get_excel_contents
)
from synesis_api.utils.file_utils import copy_file_or_directory_to_container
from synesis_api.utils.pydanticai_utils import get_model
from synesis_api.agents.data_source_analysis.output import DataSourceAnalysisAgentOutput


model = get_model()


data_source_analysis_agent = Agent(
    model,
    output_type=DataSourceAnalysisAgentOutput,
    model_settings=ModelSettings(temperature=0),
    tools=[
        execute_python_code,
        get_csv_contents,
        get_json_contents,
        get_excel_contents
    ],
    retries=5
)


@data_source_analysis_agent.system_prompt
async def get_system_prompt(ctx: RunContext[DataSourceAnalysisAgentDeps]) -> str:

    for file_path in ctx.deps.file_paths:
        _, err = await copy_file_or_directory_to_container(file_path, container_save_path=Path("/tmp") / file_path.name)

    if err:
        raise ValueError(f"Error copying file to container: {err}")

    sys_prompt = (
        f"{DATA_SOURCE_AGENT_SYSTEM_PROMPT}\n\n" +
        "The file paths to analyze are:\n\n" +
        "\n\n".join(
            [f"File path: /tmp/{file_path.name}" for file_path in ctx.deps.file_paths])
    )

    return sys_prompt


@data_source_analysis_agent.output_validator
async def validate_output(ctx: RunContext[DataSourceAnalysisAgentDeps], output: DataSourceAnalysisAgentOutput) -> DataSourceAnalysisAgentOutput:
    """
    Validate the output of the data source agent.
    """

    # Check that the source name of each data source matches a file name in the base path
    for data_source in output.data_sources:
        if data_source.source_name not in [file_path.name for file_path in ctx.deps.file_paths]:
            raise ModelRetry(
                f"The source name {data_source.source_name} does not match a file name in the base path")

    return output
