from pydantic_ai import Agent, RunContext
from pydantic_ai.models import ModelSettings

from project_server.agents.swe.prompt import SWE_AGENT_SYSTEM_PROMPT
from project_server.agents.swe.deps import SWEAgentDeps
from project_server.agents.swe.tools import (
    write_script,
    read_script,
    replace_script_lines,
    add_script_lines,
    delete_script_lines,
)
from project_server.agents.shared_tools import get_data_structures_overview_tool, get_data_structure_description_tool
from project_server.agents.swe.history_processors import keep_only_most_recent_script
from project_server.utils.pydanticai_utils import get_model
from project_server.app_secrets import SANDBOX_PYPROJECT_PATH
from project_server.agents.swe.utils import describe_available_scripts
from project_server.worker import logger

from synesis_data_structures.time_series.definitions import get_data_structure_description
from synesis_data_structures.time_series.synthetic import get_synthetic_data_description


model = get_model()


swe_agent = Agent(
    model,
    deps_type=SWEAgentDeps,
    system_prompt=SWE_AGENT_SYSTEM_PROMPT,
    tools=[
        # For now, we only allow the agent to work with a single script. Support to operate with multiple scripts may be added later
        write_script,
        read_script,
        replace_script_lines,
        add_script_lines,
        delete_script_lines,
        get_data_structures_overview_tool,
        get_data_structure_description_tool
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

    if ctx.deps.inject_synthetic_data_descriptions:
        assert ctx.deps.structure_ids_to_inject is not None, "structure_ids_to_inject must be provided if inject_synthetic_data_descriptions is True"

    env_section = f"\n\nThe pyproject.toml defining your environment is:\n\n[START_OF_PYPROJECT_TOML]{pyproject_content}[END_OF_PYPROJECT_TOML]\n\n" if pyproject_content else ""

    structure_description_section, synthetic_data_section = "", ""
    if ctx.deps.structure_ids_to_inject:
        structure_descriptions = "\n\n".join([
            get_data_structure_description(structure_id) for structure_id in ctx.deps.structure_ids_to_inject
        ])
        structure_description_section = (
            f"These are the descriptions of some relevant data structures:\n\n[START_OF_DATA_STRUCTURE_DESCRIPTIONS]{structure_descriptions}[END_OF_DATA_STRUCTURE_DESCRIPTIONS]\n\n" if structure_descriptions else ""
        )

        if ctx.deps.inject_synthetic_data_descriptions:
            synthetic_data_descriptions = "\n\n".join([
                get_synthetic_data_description(structure_id) for structure_id in ctx.deps.structure_ids_to_inject
            ])

            synthetic_data_section = (
                "Your implementation may be validated using synthetic data. Use the synthetic data to define default arguments. " +
                "For example, if we want to process a specific column in the data, there must be an argument for this, like 'target_column'. You set that variable to a default value based on the synthetic data. " +
                "Importantly, don't assume that columns with specific names exist! Just set defaults based on the synthetic data, so that running on the synthetic data with the default config works. " +
                "However, no hardcoded fields from the synthetic data outside setting default inputs, the code must be generalizable! " +
                f"The synthetic data description is:\n\n[START_OF_SYNTHETIC_DATA_DESCRIPTIONS]{synthetic_data_descriptions}[END_OF_SYNTHETIC_DATA_DESCRIPTIONS]\n\n"
            )

    script_section = ""
    if ctx.deps.functions_injected or ctx.deps.models_injected:
        script_section += f"Here are all the scripts available to you, and the docstrings for the functions and models in the scripts:\n\n{describe_available_scripts(ctx.deps.functions_injected, ctx.deps.models_injected)}"

    logger.info(
        f"SWE agent system prompt:\n\n{env_section}\n\n{structure_description_section}\n\n{synthetic_data_section}\n\n{script_section}")

    return f"{SWE_AGENT_SYSTEM_PROMPT}\n\n{env_section}\n\n{structure_description_section}\n\n{synthetic_data_section}\n\n{script_section}"
