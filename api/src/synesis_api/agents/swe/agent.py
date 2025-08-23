from pydantic_ai import Agent
from pydantic_ai.models import ModelSettings

from synesis_api.agents.swe.prompt import SWE_AGENT_SYSTEM_PROMPT
from synesis_api.agents.swe.deps import SWEAgentDeps
from synesis_api.agents.swe.tools import (
    write_script,
    replace_script_lines,
    add_script_lines,
    delete_script_lines,
)
from synesis_api.agents.swe.history_processors import keep_only_most_recent_script
from synesis_api.utils.pydanticai_utils import get_model
from synesis_data_structures.time_series.definitions import get_data_structures_overview, get_data_structure_description


model = get_model()


swe_agent = Agent(
    model,
    deps_type=SWEAgentDeps,
    system_prompt=SWE_AGENT_SYSTEM_PROMPT,
    tools=[
        # For now, we only allow the agent to work with a single script. Support to operate with multiple scripts may be added later
        write_script,
        replace_script_lines,
        add_script_lines,
        delete_script_lines,
        get_data_structures_overview,
        get_data_structure_description
        # Add extra tools during runtime with FunctionToolset
    ],
    retries=10,
    history_processors=[
        keep_only_most_recent_script,
        # summarize_message_history
    ],
    model_settings=ModelSettings(temperature=0)
    # The specific task will be provided in the user prompt
)
