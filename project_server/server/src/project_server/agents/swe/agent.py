from pydantic_ai import Agent, RunContext
from pydantic_ai.models import ModelSettings

from project_server.agents.swe.sandbox_code import get_main_skeleton
from project_server.agents.swe.prompt import SWE_AGENT_BASE_SYSTEM_PROMPT
from project_server.agents.swe.deps import SWEAgentDeps
from project_server.agents.swe.tools import (
    write_script,
    read_script,
    replace_script_lines,
    add_script_lines,
    delete_script_lines,
    search_existing_functions
)
from project_server.agents.shared_tools import (
    get_data_structures_overview_tool,
    get_data_structure_description_tool,
    get_task_guidelines_tool,
    get_synthetic_data_description_tool,
    get_data_sources_overview_tool,
    get_data_source_description_tool
)
from project_server.agents.swe.history_processors import keep_only_most_recent_script
from project_server.utils.pydanticai_utils import get_model
from project_server.app_secrets import SANDBOX_PYPROJECT_PATH, MODELS_MODULE, MODELS_MODULE_TMP, FUNCTIONS_MODULE_TMP, PIPELINES_MODULE_TMP, DATA_INTEGRATION_MODULE_TMP
from project_server.worker import logger
from project_server.agents.swe.utils import save_script_with_version_handling
from project_server.utils.data_utils import get_structure_descriptions_from_datasets, get_data_source_type_descriptions_from_data_sources


model = get_model()


swe_agent = Agent(
    model,
    deps_type=SWEAgentDeps,
    system_prompt=SWE_AGENT_BASE_SYSTEM_PROMPT,
    tools=[
        # For now, we only allow the agent to work with a single script. Support to operate with multiple scripts may be added later
        write_script,
        read_script,
        replace_script_lines,
        add_script_lines,
        delete_script_lines,
        get_data_structures_overview_tool,
        get_data_structure_description_tool,
        get_data_sources_overview_tool,
        get_data_source_description_tool,
        get_task_guidelines_tool,
        get_synthetic_data_description_tool,
        search_existing_functions

    ],
    retries=10,
    history_processors=[keep_only_most_recent_script],
    model_settings=ModelSettings(temperature=0)
    # The specific task will be provided in the user prompt
)


@swe_agent.system_prompt
async def swe_agent_system_prompt(ctx: RunContext[SWEAgentDeps]) -> str:

    if not ctx.deps:
        return SWE_AGENT_BASE_SYSTEM_PROMPT

    data_sources_description = "\n\n".join(
        [data_source.description_for_agent for data_source in ctx.deps.data_sources_injected])
    datasets_description = "\n\n".join(
        [dataset.description_for_agent for dataset in ctx.deps.datasets_injected])
    model_entities_description = "\n\n".join(
        [model_entity.description_for_agent for model_entity in ctx.deps.model_entities_injected])

    data_sources_section = f"The input data sources are:\n\n{data_sources_description}\n\n"
    datasets_section = f"The input datasets are:\n\n{datasets_description}\n\n"
    model_entities_section = f"The input model entities are:\n\n{model_entities_description}\n\n".replace(
        MODELS_MODULE, MODELS_MODULE_TMP)

    structure_descriptions = get_structure_descriptions_from_datasets(
        ctx.deps.datasets_injected)
    data_source_type_descriptions = get_data_source_type_descriptions_from_data_sources(
        ctx.deps.data_sources_injected)

    structure_section = f"The descriptions of the relevant Kvasir data structures are:\n\n{structure_descriptions}\n\n"
    data_source_type_section = f"The descriptions of the relevant Kvasir data source types are:\n\n{data_source_type_descriptions}\n\n"

    skeleton_code = get_main_skeleton(
        data_sources=ctx.deps.data_sources_injected,
        datasets=ctx.deps.datasets_injected,
        model_entities=ctx.deps.model_entities_injected,
    )

    storage = save_script_with_version_handling(
        ctx, "implementation.py", skeleton_code, "pipeline")

    skeleton_section = (
        f"We have created a script called {storage.filename} with skeleton code to get you started. " +
        "The code loads the inputs of the pipeline. All object groups in the datasets are provided, though you may only have use for a subset of them. " +
        f"This is the current {storage.filename}: <begin_script file_name='{storage.filename}'>\n\n{skeleton_code}\n\n<end_script>\n\n"
    )

    with open(SANDBOX_PYPROJECT_PATH, "r") as file:
        pyproject_content = file.read()

    env_section = f"\n\nThe pyproject.toml defining your environment is:\n\n[START_OF_PYPROJECT_TOML]{pyproject_content}[END_OF_PYPROJECT_TOML]\n\n" if pyproject_content else ""

    full_prompt = (
        f"{SWE_AGENT_BASE_SYSTEM_PROMPT}\n\n+" +
        f"{env_section}\n\n" +
        f"{model_entities_section}\n\n" +
        f"{data_source_type_section}\n\n" +
        f"{structure_section}\n\n" +
        f"{data_sources_section}\n\n" +
        f"{datasets_section}\n\n" +
        f"{skeleton_section}" +
        "NB: You must import from the _tmp modules as we are in development mode. " +
        f"This means {MODELS_MODULE_TMP} for models, {FUNCTIONS_MODULE_TMP} for functions, {PIPELINES_MODULE_TMP} for pipelines, and {DATA_INTEGRATION_MODULE_TMP} for data integration."
    )

    logger.info(
        f"SWE agent system prompt:\n\n{full_prompt}")

    return full_prompt
