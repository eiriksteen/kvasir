import uuid
from pydantic import BaseModel, Field
from pydantic_ai import Agent, RunContext, ModelRetry
from pydantic_ai.settings import ModelSettings
from dataclasses import dataclass, field
from typing import List, Optional


from project_server.utils.code_utils import run_python_code_in_container
from project_server.agents.analysis.prompt import ANALYSIS_HELPER_SYSTEM_PROMPT
from project_server.utils.agent_utils import (
    get_model,
    get_entities_description,
    get_sandbox_environment_description,
)
from project_server.client import ProjectClient
from project_server.agents.analysis.deps import AnalysisDeps
from project_server.agents.chart.agent import chart_agent
from project_server.agents.chart.deps import ChartDeps
from project_server.app_secrets import AGENT_OUTPUTS_INTERNAL_DIR
from pathlib import Path
from project_server.utils.docker_utils import check_file_exists_in_container, write_file_to_container

model = get_model()


class CodeRun(BaseModel):
    code: str
    output: str


class ChartAttached(BaseModel):
    chart_description: str
    chart_script_path: str


@dataclass
class HelperAgentDeps:
    client: ProjectClient
    container_name: str
    project_id: uuid.UUID
    analysis_id: uuid.UUID
    analysis_result_id: uuid.UUID
    data_sources_injected: List[uuid.UUID] = field(default_factory=list)
    datasets_injected: List[uuid.UUID] = field(default_factory=list)
    analyses_injected: List[uuid.UUID] = field(default_factory=list)
    model_entities_injected: List[uuid.UUID] = field(default_factory=list)

    # Outputs of the tool calls
    code: Optional[str] = None
    charts: List[ChartAttached] = field(default_factory=list)
    tables: List[str] = field(default_factory=list)
    images: List[str] = field(default_factory=list)


class HelperAgentOutput(BaseModel):
    analysis: str = Field(
        description="This should be a short explanation and interpretation of the result of the analysis. This should be in github flavored markdown format.")
    code: Optional[str] = Field(
        description="The code that was executed to generate the analysis.")
    charts: List[ChartAttached] = Field(
        description="The charts that were attached to the analysis.")
    tables: List[str] = Field(
        description="The tables that were attached to the analysis.")
    images: List[str] = Field(
        description="The images that were attached to the analysis.")


analysis_helper_agent = Agent(
    model,
    system_prompt=ANALYSIS_HELPER_SYSTEM_PROMPT,
    name="Analysis Helper Agent",
    model_settings=ModelSettings(temperature=0.1),
    retries=3,
    deps_type=HelperAgentDeps
)


@analysis_helper_agent.system_prompt
async def analysis_helper_agent_system_prompt(ctx: RunContext[HelperAgentDeps]) -> str:

    entities_description = await get_entities_description(
        ctx.deps.client,
        ctx.deps.data_sources_injected,
        ctx.deps.datasets_injected,
        ctx.deps.model_entities_injected,
        ctx.deps.analyses_injected,
        []  # pipelines
    )

    env_description = get_sandbox_environment_description()

    return f"""{ANALYSIS_HELPER_SYSTEM_PROMPT}
        \n\n{env_description}
        \n\n{entities_description}
    """


@analysis_helper_agent.tool()
async def run_python_code(ctx: RunContext[HelperAgentDeps], python_code: str) -> str:
    """
    Run python code in a container and return the output.
    Args:
        ctx: The context of the agent.
        python_code: The python code to run.
    Returns:
        The output of the python code (truncated if too long).
    """
    out, err = await run_python_code_in_container(python_code, ctx.deps.container_name)

    if err:
        return f"You got the following error: {err}"

    ctx.deps.code = python_code

    # Truncate output to avoid excessive length
    MAX_OUTPUT_LENGTH = 5000
    if len(out) > MAX_OUTPUT_LENGTH:
        truncated_output = out[:MAX_OUTPUT_LENGTH]
        return f"{truncated_output}\n\n... [Output truncated. Total length: {len(out)} characters]"

    return out


@analysis_helper_agent.tool()
async def prepare_result_image(
    ctx: RunContext[HelperAgentDeps],
    image_path: str
) -> str:
    """
    Prepare an image file to be attached to the analysis result.

    The image must already exist in the project container at the specified path.
    Supported formats: png, jpg, jpeg, gif, svg, webp

    Args:
        ctx: The analysis context
        image_path: Path to the image file in the container (e.g., "/workspace/plots/chart.png")

    Returns:
        Success message
    """
    # Validate path
    path = Path(image_path)

    # Check file exists
    exists = await check_file_exists_in_container(path, ctx.deps.container_name)
    if not exists:
        raise ModelRetry(
            f"Image file does not exist at path: {image_path}. "
            f"Please create the image file first or provide the correct path."
        )

    # Validate file extension
    allowed_extensions = ['.png', '.jpg', '.jpeg', '.gif', '.svg', '.webp']
    if path.suffix.lower() not in allowed_extensions:
        raise ModelRetry(
            f"Invalid image file type: {path.suffix}. "
            f"Allowed types: {', '.join(allowed_extensions)}. "
            f"Please save your image in one of these formats."
        )

    ctx.deps.images.append(image_path)
    return f"Successfully prepared image at {image_path}"


@analysis_helper_agent.tool()
async def prepare_result_chart(
    ctx: RunContext[HelperAgentDeps],
    chart_description: str,
    datasets_to_use: List[uuid.UUID],
    data_sources_to_use: List[uuid.UUID],
) -> str:
    """
    Generate an ECharts visualization script to be attached to the analysis result. 
    The chart agent will base its chart on the code you generated in the past tool call. 

    This will invoke the chart generation agent to create a chart script that
    outputs ECharts configuration JSON.

    Args:
        ctx: The analysis context
        chart_description: Description of what chart to create (e.g., "Line chart showing temperature over time")
        datasets_to_use: List of dataset IDs to use for the chart
        data_sources_to_use: List of data source IDs to use for the chart

    Returns:
        Success message with the script path
    """
    try:
        # Generate the chart script using the chart agent
        chart_result = await chart_agent.run(
            chart_description,
            deps=ChartDeps(
                container_name=ctx.deps.container_name,
                client=ctx.deps.client,
                project_id=ctx.deps.project_id,
                datasets_injected=datasets_to_use,
                data_sources_injected=data_sources_to_use,
                base_code=ctx.deps.code
            )
        )

        # Save the script to a unique path
        script_filename = f"analysis_chart_{ctx.deps.analysis_result_id}.py"
        save_path = AGENT_OUTPUTS_INTERNAL_DIR / script_filename
        await write_file_to_container(save_path, chart_result.output.script_content, ctx.deps.container_name)
        ctx.deps.charts.append(ChartAttached(
            chart_description=chart_description, chart_script_path=str(save_path)))

        return f"Successfully prepared chart script at {save_path}"

    except Exception as e:
        raise ModelRetry(f"Failed to create chart: {str(e)}")


@analysis_helper_agent.tool()
async def prepare_result_table(
    ctx: RunContext[HelperAgentDeps],
    table_path: str
) -> str:
    """
    Prepare a table (parquet file) to be attached to the analysis result. 

    The parquet file must already exist in the project container at the specified path.

    Args:
        ctx: The analysis context
        table_path: Path to the parquet file in the container (e.g., "/workspace/tables/results.parquet")

    Returns:
        Success message
    """
    # Validate path
    path = Path(table_path)

    # Check file exists
    exists = await check_file_exists_in_container(path, ctx.deps.container_name)
    if not exists:
        raise ModelRetry(
            f"Table file does not exist at path: {table_path}. "
            f"Please create the parquet file first or provide the correct path."
        )

    # Validate file extension
    if path.suffix.lower() != '.parquet':
        raise ModelRetry(
            f"Invalid table file type: {path.suffix}. Expected .parquet format. "
            f"Please save your table as a parquet file using df.to_parquet('{table_path}')."
        )

    ctx.deps.tables.append(table_path)
    return f"Successfully prepared table at {table_path}"


@analysis_helper_agent.output_validator
async def submit_analysis_output(ctx: RunContext[HelperAgentDeps], analysis: str) -> HelperAgentOutput:
    """"
    Submit the analysis output.
    Args:
        ctx: The context of the agent.
        analysis: This should be a short explanation and interpretation of the result of the analysis. This should be in github flavored markdown format..
    Returns:
        The analysis output.
    """

    return HelperAgentOutput(
        analysis=analysis,
        code=ctx.deps.code,
        charts=ctx.deps.charts,
        tables=ctx.deps.tables,
        images=ctx.deps.images
    )
