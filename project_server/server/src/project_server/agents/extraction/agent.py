from pydantic_ai import Agent, RunContext
from pydantic_ai.models import ModelSettings

from project_server.agents.extraction.deps import ExtractionDeps
from project_server.agents.extraction.tools import schema_toolset, submission_toolset
from project_server.agents.shared_tools import navigation_toolset, execute_python_code
from project_server.agents.extraction.prompt import EXTRACTION_AGENT_SYSTEM_PROMPT
from project_server.utils.agent_utils import get_model, get_project_description, get_working_directory_description
from project_server.worker import logger


model = get_model()


extraction_agent = Agent[ExtractionDeps, str](
    model,
    deps_type=ExtractionDeps,
    system_prompt=EXTRACTION_AGENT_SYSTEM_PROMPT,
    tools=[execute_python_code],
    toolsets=[navigation_toolset, submission_toolset, schema_toolset],
    model_settings=ModelSettings(temperature=0),
    retries=3
)


@extraction_agent.system_prompt
async def extraction_agent_system_prompt(ctx: RunContext[ExtractionDeps]) -> str:

    if not ctx.deps:
        return EXTRACTION_AGENT_SYSTEM_PROMPT

    project_description = get_project_description(ctx.deps.project)
    working_directory_section = await get_working_directory_description(ctx.deps.container_name)

    full_prompt = (
        f"{EXTRACTION_AGENT_SYSTEM_PROMPT}\n\n" +
        f"{project_description}\n\n"
        f"{working_directory_section}\n\n"
    )

    logger.info(
        f"Extraction agent system prompt:\n\n{full_prompt}")

    return full_prompt
