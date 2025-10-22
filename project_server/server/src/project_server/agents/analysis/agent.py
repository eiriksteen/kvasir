from pydantic_ai import Agent
from pydantic_ai.settings import ModelSettings
from pydantic_ai import RunContext
from project_server.agents.analysis.prompt import ANALYSIS_AGENT_SYSTEM_PROMPT
from project_server.utils.pydanticai_utils import get_model
from project_server.agents.analysis.deps import AnalysisDeps
from project_server.agents.analysis.tools import (
    search_through_datasets,
    search_through_data_sources,
    search_through_analyses,
    search_through_analysis_results,
    search_knowledge_bank,
    add_analysis_result_to_notebook_section,
    create_notebook_section,
    move_analysis_result,
    delete_notebook_section,
    edit_section_name,
    move_sections,
    create_empty_analysis_result,
    generate_analysis_result,
    plot_analysis_result,
    create_table_for_analysis_result,
)
from project_server.worker import logger


model = get_model()

analysis_agent = Agent(
    model,
    system_prompt=ANALYSIS_AGENT_SYSTEM_PROMPT,
    deps_type=AnalysisDeps,
    name="Analysis Agent",
    model_settings=ModelSettings(temperature=0.1),
    retries=3,
    tools=[
        search_through_datasets,
        search_through_data_sources,
        search_through_analyses,
        search_through_analysis_results,
        search_knowledge_bank,
        add_analysis_result_to_notebook_section,
        create_notebook_section,
        move_analysis_result,
        delete_notebook_section,
        edit_section_name,
        move_sections,
        create_empty_analysis_result,
        generate_analysis_result,
        plot_analysis_result,
        create_table_for_analysis_result,
    ],
)


@analysis_agent.system_prompt
async def analysis_agent_system_prompt(ctx: RunContext[AnalysisDeps]) -> str:
    if not ctx.deps:
        return ANALYSIS_AGENT_SYSTEM_PROMPT

    data_sources_description = "\n\n".join(
        [data_source.description_for_agent for data_source in ctx.deps.data_sources_injected])
    datasets_description = "\n\n".join(
        [dataset.description_for_agent for dataset in ctx.deps.datasets_injected])
    model_entities_description = "\n\n".join(
        [model_entity.description_for_agent for model_entity in ctx.deps.model_entities_injected])

    data_sources_section = f"The input data sources are:\n\n{data_sources_description}\n\n"
    datasets_section = f"The input datasets are:\n\n{datasets_description}\n\n"
    model_entities_section = f"The input model entities are:\n\n{model_entities_description}\n\n"

    final_prompt = (
        f"{ANALYSIS_AGENT_SYSTEM_PROMPT}\n\n{data_sources_section}{datasets_section}{model_entities_section}"
    )

    logger.info(f"Analysis agent system prompt: {final_prompt}")

    return final_prompt
