from pydantic_ai import Agent
from pydantic_ai.settings import ModelSettings

from synesis_api.modules.orchestrator.agent.prompt import ORCHESTRATOR_SYSTEM_PROMPT
from synesis_api.utils.pydanticai_utils import get_model
# from synesis_api.modules.orchestrator.agent.output import (
#     NoHandoffOutput,
#     AnalysisHandoffOutput,
#     PipelineHandoffOutput,
#     DataIntegrationHandoffOutput,
#     ModelIntegrationHandoffOutput
# )
from synesis_api.modules.orchestrator.agent.tools import (
    search_existing_models,
    add_model_entity_to_project,
    get_task_guidelines_tool
)


model = get_model()


orchestrator_agent = Agent(
    model,
    system_prompt=ORCHESTRATOR_SYSTEM_PROMPT,
    model_settings=ModelSettings(temperature=0.0),
    tools=[
        search_existing_models,
        add_model_entity_to_project,
        get_task_guidelines_tool
    ],
    # output_type defined when running
)
