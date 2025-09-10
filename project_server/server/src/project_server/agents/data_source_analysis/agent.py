from pydantic_ai import Agent, RunContext
from pydantic_ai.settings import ModelSettings

from project_server.agents.data_source_analysis.deps import DataSourceAnalysisAgentDeps
from project_server.agents.data_source_analysis.prompt import DATA_SOURCE_AGENT_SYSTEM_PROMPT
from project_server.utils.pydanticai_utils import get_model
from project_server.agents.data_source_analysis.output import TabularFileAnalysisOutput


model = get_model()


data_source_analysis_agent = Agent(
    model,
    # TODO: Support multiple data sources
    output_type=[TabularFileAnalysisOutput],
    model_settings=ModelSettings(temperature=0),
    retries=5
)


@data_source_analysis_agent.system_prompt
async def get_system_prompt(ctx: RunContext[DataSourceAnalysisAgentDeps]) -> str:

    sys_prompt = (
        f"{DATA_SOURCE_AGENT_SYSTEM_PROMPT}\n\n" +
        f"The file path to analyze is: {ctx.deps.file_path}"
    )

    return sys_prompt
