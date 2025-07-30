from pathlib import Path
from typing import List, Literal
from dataclasses import dataclass
from pydantic_ai import Agent, ModelRetry, RunContext
from pydantic_ai.settings import ModelSettings
from synesis_api.agents.data_integration.data_source_analysis_agent.prompt import DATA_SOURCE_AGENT_SYSTEM_PROMPT
from synesis_api.agents.data_integration.shared_tools import (
    execute_python_code,
    get_csv_contents,
    get_json_contents,
    get_excel_contents
)
# from synesis_api.agents.data_integration.data_source_agent.utils import list_directory_contents, resolve_path_from_directory_name
from synesis_api.utils import (
    copy_file_or_directory_to_container,
    get_model,
)
from synesis_api.base_schema import BaseSchema


@dataclass
class DataSourceAnalysisAgentDeps:
    file_paths: List[Path]
    # TODO: Add other sources and corresponding deps to interact with them
    # s3_buckets = ...


class FeatureDescription(BaseSchema):
    name: str
    unit: str
    description: str
    type: Literal["numerical", "categorical"]
    subtype: Literal["continuous", "discrete"]
    scale: Literal["ratio", "interval", "ordinal", "nominal"]


class DataSourceDescription(BaseSchema):
    source_name: str
    content_description: str
    quality_description: str
    num_rows: int
    features: List[FeatureDescription]


class DataSourceAnalysisAgentOutput(BaseSchema):
    data_sources: List[DataSourceDescription]


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
