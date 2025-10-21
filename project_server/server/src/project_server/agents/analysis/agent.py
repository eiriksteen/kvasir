from pydantic_ai import Agent
from pydantic_ai.settings import ModelSettings

from project_server.agents.analysis.prompt import ANALYSIS_AGENT_SYSTEM_PROMPT
from project_server.utils.pydanticai_utils import get_model
from project_server.agents.analysis.deps import AnalysisDeps
from project_server.agents.analysis.tools import (
    search_through_datasets,
    search_through_data_sources,
    search_through_analysis_objects,
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
        search_through_analysis_objects,
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
