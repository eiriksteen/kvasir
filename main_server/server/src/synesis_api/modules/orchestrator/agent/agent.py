from pydantic_ai import Agent, FunctionToolset
from pydantic_ai.settings import ModelSettings

from synesis_api.modules.orchestrator.agent.prompt import ORCHESTRATOR_SYSTEM_PROMPT
from synesis_api.utils.pydanticai_utils import get_model
from synesis_api.modules.orchestrator.agent.tools import (
    submit_run_for_swe_agent,
    submit_run_for_analysis_agent,
    get_entity_details_tool
)
from synesis_api.modules.orchestrator.agent.history_processors import (
    keep_only_most_recent_context,
    keep_only_most_recent_project_desc,
    keep_only_most_recent_run_status
)


model = get_model()

orchestrator_agent = Agent(
    model,
    system_prompt=ORCHESTRATOR_SYSTEM_PROMPT,
    model_settings=ModelSettings(temperature=0.0),
    retries=3,
    history_processors=[
        keep_only_most_recent_context,
        keep_only_most_recent_project_desc,
        keep_only_most_recent_run_status
    ]
    # output_type defined when running
)


# Define like this since we want to inject during runs
# The orchestrator should not always have access to tools
orchestrator_toolset = FunctionToolset(
    tools=[
        submit_run_for_swe_agent,
        submit_run_for_analysis_agent,
        get_entity_details_tool
    ]
)
