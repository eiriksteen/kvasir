from pydantic_ai import Agent, RunContext
from pydantic_ai.settings import ModelSettings

from project_server.agents.data_integration.deps import DataIntegrationAgentDeps
from project_server.agents.data_integration.prompt import DATASET_INTEGRATION_SYSTEM_PROMPT
from project_server.agents.shared_tools import execute_python_code
from project_server.agents.shared_tools import get_data_structures_overview_tool, get_data_structure_description_tool
from project_server.utils.pydanticai_utils import get_model
from project_server.agents.data_integration.output import submit_data_integration_output

model = get_model()


data_integration_agent = Agent(
    model,
    output_type=submit_data_integration_output,
    model_settings=ModelSettings(temperature=0),
    tools=[
        execute_python_code,
        get_data_structures_overview_tool,
        get_data_structure_description_tool
    ],
    retries=5
)


@data_integration_agent.system_prompt
async def get_system_prompt(ctx: RunContext[DataIntegrationAgentDeps]) -> str:

    sys_prompt = (
        f"{DATASET_INTEGRATION_SYSTEM_PROMPT}\n\n" +
        f"The data sources are:\n\n" +
        f"{'\n\n'.join([str(ds) for ds in ctx.deps.data_sources])}\n\n" +
        f"The target data description is provided by the user in the prompt."
    )

    return sys_prompt
