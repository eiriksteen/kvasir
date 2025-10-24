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
from project_server.utils.agent_utils import (
    get_model,
    get_injected_entities_description,
    get_sandbox_environment_description,
    get_structure_descriptions_from_datasets,
    get_data_source_type_descriptions_from_data_sources
)
from project_server.app_secrets import MODELS_MODULE_TMP, FUNCTIONS_MODULE_TMP, PIPELINES_MODULE_TMP, DATA_INTEGRATION_MODULE_TMP
from project_server.worker import logger
from project_server.agents.swe.utils import save_script_with_version_handling


model = get_model()


swe_agent = Agent(
    model,
    deps_type=SWEAgentDeps,
    system_prompt=SWE_AGENT_BASE_SYSTEM_PROMPT,
    tools=[
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
)


@swe_agent.system_prompt
async def swe_agent_system_prompt(ctx: RunContext[SWEAgentDeps]) -> str:

    if not ctx.deps:
        return SWE_AGENT_BASE_SYSTEM_PROMPT

    entities_description = get_injected_entities_description(
        ctx.deps.data_sources_injected,
        ctx.deps.datasets_injected,
        ctx.deps.model_entities_injected,
        ctx.deps.analyses_injected,
        tmp=True
    )

    data_structure_descriptions = get_structure_descriptions_from_datasets(
        ctx.deps.datasets_injected)

    data_source_type_descriptions = get_data_source_type_descriptions_from_data_sources(
        ctx.deps.data_sources_injected)

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

    env_description = get_sandbox_environment_description()

    full_prompt = (
        f"{SWE_AGENT_BASE_SYSTEM_PROMPT}\n\n" +
        f"{env_description}\n\n" +
        f"{entities_description}\n\n" +
        f"{data_structure_descriptions}\n\n" +
        f"{data_source_type_descriptions}\n\n" +
        f"{skeleton_section}\n\n" +
        "NB: You must import from the _tmp modules as we are in development mode. " +
        f"This means {MODELS_MODULE_TMP} for models, {FUNCTIONS_MODULE_TMP} for functions, {PIPELINES_MODULE_TMP} for pipelines, and {DATA_INTEGRATION_MODULE_TMP} for data integration."
    )

    logger.info(
        f"SWE agent system prompt:\n\n{full_prompt}")

    return full_prompt
