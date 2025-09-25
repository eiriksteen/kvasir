from pydantic_ai import Agent, RunContext
from pydantic_ai.models import ModelSettings

from project_server.agents.swe.prompt import SWE_AGENT_SYSTEM_PROMPT
from project_server.agents.swe.deps import SWEAgentDeps
from project_server.agents.swe.tools import (
    write_script,
    replace_script_lines,
    add_script_lines,
    delete_script_lines,
    switch_script,
)
from project_server.agents.swe.history_processors import keep_only_most_recent_script
from project_server.utils.pydanticai_utils import get_model
from project_server.app_secrets import SANDBOX_PYPROJECT_PATH
from synesis_data_structures.time_series.definitions import get_data_structure_description


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
        switch_script,
        # get_data_structures_overview,
        # get_data_structure_description
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


@swe_agent.system_prompt
def swe_agent_system_prompt(ctx: RunContext[SWEAgentDeps]) -> str:
    with open(SANDBOX_PYPROJECT_PATH, "r") as file:
        pyproject_content = file.read()

    structure_descriptions = None
    if ctx.deps.structure_ids_to_inject:
        structure_descriptions = "\n\n".join([
            get_data_structure_description(structure_id) for structure_id in ctx.deps.structure_ids_to_inject
        ])

    return (
        SWE_AGENT_SYSTEM_PROMPT +
        f"\n\nThe pyproject.toml defining your environment is:\n\n[START_OF_PYPROJECT_TOML]{pyproject_content}[END_OF_PYPROJECT_TOML]\n\n" +
        (f"These are the descriptions of some relevant data structures:\n\n[START_OF_DATA_STRUCTURE_DESCRIPTIONS]{structure_descriptions}[END_OF_DATA_STRUCTURE_DESCRIPTIONS]" if structure_descriptions else "")
    )
