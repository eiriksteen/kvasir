from pydantic_ai import Agent
from pydantic_ai.settings import ModelSettings

from project_server.agents.pipeline.prompt import PIPELINE_AGENT_SYSTEM_PROMPT
from project_server.utils.pydanticai_utils import get_model

from project_server.agents.shared_tools import (
    get_data_structures_overview_tool,
    get_data_structure_description_tool
)


model = get_model()


pipeline_agent = Agent(
    model,
    system_prompt=PIPELINE_AGENT_SYSTEM_PROMPT,
    model_settings=ModelSettings(temperature=0.0),
    tools=[get_data_structures_overview_tool,
           get_data_structure_description_tool],
    retries=3
)
