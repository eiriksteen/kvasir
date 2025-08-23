from pydantic_ai import Agent
from pydantic_ai.models import ModelSettings

from synesis_api.agents.model_integration.deps import ModelIntegrationDeps
from synesis_api.agents.model_integration.implementation_agent.prompt import IMPLEMENTATION_SYSTEM_PROMPT
from synesis_api.agents.model_integration.shared_tools import (
    get_repo_info,
    get_repo_structure,
    get_file_content,
    write_script,
    replace_script_lines,
    add_script_lines,
    delete_script_lines,
)
from synesis_api.agents.model_integration.prepare_tools import filter_tools
from synesis_api.agents.model_integration.history_processors import keep_only_most_recent_script
from synesis_api.agents.model_integration.implementation_agent.output import (
    submit_model_analysis_output,
    submit_implementation_planning_output,
    submit_training_output,
    submit_inference_output
)
from synesis_api.utils.pydanticai_utils import get_model


model = get_model()


implementation_agent = Agent(
    model,
    system_prompt=IMPLEMENTATION_SYSTEM_PROMPT,
    deps_type=ModelIntegrationDeps,
    output_type=[
        submit_model_analysis_output,
        submit_implementation_planning_output,
        submit_training_output,
        submit_inference_output
    ],
    tools=[
        get_repo_info,
        get_repo_structure,
        get_file_content,
        write_script,
        replace_script_lines,
        add_script_lines,
        delete_script_lines
    ],
    prepare_tools=filter_tools,
    retries=10,
    history_processors=[
        keep_only_most_recent_script,
        # summarize_message_history
    ],
    model_settings=ModelSettings(temperature=0),
)
