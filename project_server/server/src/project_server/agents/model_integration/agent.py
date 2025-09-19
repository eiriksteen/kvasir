import uuid
from pydantic_ai import Agent
from pydantic_ai.settings import ModelSettings

from project_server.utils.pydanticai_utils import get_model
from project_server.agents.model_integration.prompt import MODEL_INTEGRATION_AGENT_SYSTEM_PROMPT
from project_server.agents.model_integration.output import (
    ModelDescription,
    ImplementationFeedbackOutput,
)
from project_server.agents.shared_tools import (
    get_data_structures_overview_tool,
    get_data_structure_description_tool
)
from synesis_schemas.main_server import SearchModelSourcesRequest, ModelSourceCreate


model = get_model()


model_integration_agent = Agent(
    model,
    system_prompt=MODEL_INTEGRATION_AGENT_SYSTEM_PROMPT,
    model_settings=ModelSettings(temperature=0.0),
    tools=[get_data_structures_overview_tool,
           get_data_structure_description_tool],
    # output_type=[
    #     SearchModelSourcesRequest,
    #     ModelSourceCreate,
    #     uuid.UUID,
    #     ModelDescription,
    #     ImplementationFeedbackOutput,
    # ],
    retries=3
)
