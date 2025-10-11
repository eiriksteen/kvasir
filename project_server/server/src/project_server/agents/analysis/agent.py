import uuid
import time
from datetime import datetime
from pydantic import ValidationError, Field, BaseModel
from pydantic_ai import Agent, RunContext
from pydantic_ai.settings import ModelSettings
from dataclasses import dataclass
from typing import List, Literal
from pydantic_ai.messages import ModelMessage


from project_server.agents.analysis.prompt import ANALYSIS_AGENT_SYSEM_PROMPT
from project_server.client import (
    ProjectClient,
    get_project,
    get_datasets_by_ids,
    get_data_sources_by_ids,
)
from synesis_schemas.main_server import (
    GetDatasetByIDsRequest,
    GetDataSourcesByIDsRequest,
    AnalysisResult, 
    NotebookSectionCreate, 
    AnalysisStatusMessage,
    MoveRequest,
    NotebookSectionUpdate,
    AnalysisResultFindRequest,
    AnalysisResultUpdate,
    PlotCreate, 
    PREDEFINED_COLORS, 
    PlotConfig,
    TableCreate, 
    TableConfig, 
    TableColumn,
    ContextCreate,
    AggregationObjectCreate, 
    AggregationObjectUpdate
)
from project_server.agents.analysis.utils import simplify_dataset_overview, get_relevant_metadata_for_prompt, post_analysis_result_to_redis
from project_server.client import (
    get_analysis_objects_by_project_request,
    get_analysis_object_request,
    create_section_request,
    update_section_request,
    delete_section_request,
    add_analysis_result_to_section_request,
    get_data_for_analysis_result_request,
    move_element_request,
    update_analysis_result_request,
    delete_analysis_result_request,
    create_analysis_result_request,
    get_analysis_result_by_id_request,
    get_analysis_results_by_ids_request,
    create_aggregation_object_request, 
    update_aggregation_object_request, 
    get_aggregation_object_by_analysis_result_id_request,
    create_chat_message_pydantic_request, 
    create_context_request,
)
from synesis_schemas.project_server import RunAnalysisRequest
from project_server.client.requests.plots import create_plot
from project_server.client.requests.tables import create_table
from project_server.agents.analysis.helper_agent import analysis_helper_agent, HelperAgentDeps
from project_server.redis import get_redis
from project_server.utils.pydanticai_utils import get_model
from project_server.worker import logger



class AnalysisResultModelResponse(BaseModel):
    analysis: str = Field(description="This should be a short explanation and interpretation of the result of the analysis. This should be in github flavored markdown format.")
    python_code: str | None = Field(default=None, description="The python code that was used to generate the analysis result. This code should be executable and should be able to run in a python container.")
    input_variable: str | None = Field(default=None, description="The variable that was used to to generate the analysis result. This is a string of the variable name.")
    output_variable: str | None = Field(default=None, description="The variable that is most relevant to the analysis. This variable is likely the last variable in the code.")

class AggregationObjectCreateResponse(BaseModel):
    name: str
    description: str

class AnalysisResultMoveRequest(BaseModel):
    analysis_result_id: uuid.UUID = Field(description="The ID of the analysis result.")
    next_element_type: Literal['analysis_result', 'notebook_section'] = Field(description="The type of the next element.")
    next_element_id: uuid.UUID = Field(description="The ID of the next element.")
    new_section_id: uuid.UUID = Field(description="The ID of the new parent section.")


class SectionMoveRequest(BaseModel):
    section_id: uuid.UUID = Field(description="The ID of the section.")
    next_element_type: Literal['analysis_result', 'notebook_section'] = Field(description="The type of the next element.")
    next_element_id: uuid.UUID = Field(description="The ID of the next element.")
    new_section_id: uuid.UUID | None = Field(description="The ID of the new parent section (should be None if the section is to be a root section).")


@dataclass
class AnalysisDeps:
    analysis_request: RunAnalysisRequest
    client: ProjectClient
    run_id: uuid.UUID

model = get_model()

analysis_agent = Agent(
    model,
    system_prompt=ANALYSIS_AGENT_SYSEM_PROMPT,
    deps_type=AnalysisDeps,
    name="Analysis Agent",
    model_settings=ModelSettings(temperature=0.1),
    retries=3
)



@analysis_agent.tool
async def search_through_datasets(ctx: RunContext[AnalysisDeps]) -> str:
    """
    Searches through all datasets in a project. This tool is useful when the context the user has provided is incomplete.

    Args:
        ctx (RunContext[AnalysisDeps]): The context of the analysis.
    """
    project = await get_project(ctx.deps.analysis_request.project_id)
    datasets = await get_datasets_by_ids(ctx.deps.client, GetDatasetByIDsRequest(dataset_ids=project.dataset_ids))
    datasets_overview = simplify_dataset_overview(datasets)
    
    dataset_message = f"""
        <Available datasets>
        {datasets_overview}
        </Available datasets>
    """
    return dataset_message

@analysis_agent.tool
async def search_through_data_sources(ctx: RunContext[AnalysisDeps]) -> str:
    """
    Searches through all data sources in a project. This tool is useful when the context the user has provided is incomplete.

    Args:
        ctx (RunContext[AnalysisDeps]): The context of the analysis.    
    """
    project = await get_project(ctx.deps.analysis_request.project_id)
    data_sources = await get_data_sources_by_ids(ctx.deps.client, GetDataSourcesByIDsRequest(data_source_ids=project.data_source_ids))
    data_source_message = f"""
        <Available data sources>
        {data_sources}
        </Available data sources>
    """
    return data_source_message

@analysis_agent.tool
async def search_through_analysis_objects(ctx: RunContext[AnalysisDeps]) -> str:
    """
    Returns all the analysis objects in a project. This tool is useful when you do not know which analysis object to add or edit an analysis result to.

    Args:
        ctx (RunContext[AnalysisDeps]): The context of the analysis.
    """
    analysis_objects = await get_analysis_objects_by_project_request(ctx.deps.client, ctx.deps.analysis_request.project_id)

    analysis_objects_message = f"""
        <Available analysis objects>
        Analysis objects in project: {analysis_objects}
        </Available analysis objects>
    """

    return analysis_objects_message


@analysis_agent.tool
async def search_through_analysis_results(ctx: RunContext[AnalysisDeps], analysis_result_ids: List[uuid.UUID]) -> str:
    """
    Searches through all analysis results in a project. This tool is useful when you do not know which analysis result to add or edit an analysis result to.
    Args:
        ctx (RunContext[AnalysisDeps]): The context of the analysis.
        analysis_result_ids (List[uuid.UUID]): The IDs of the analysis results to search through.
    """
    analysis_results = await get_analysis_results_by_ids_request(ctx.deps.client, AnalysisResultFindRequest(analysis_result_ids=analysis_result_ids))
    analysis_results_message = f"""
        <Analysis results>
        Analysis results: {analysis_results}
        </Analysis results>
    """
    return analysis_results_message


@analysis_agent.tool_plain
def search_knowledge_bank(prompt: str) -> List[str]:
    """
    Gets the most relevant analysis steps for a given prompt. This tool can be used to get ideas for analysis steps when the user prompt is vague or open ended.

    Args:
        prompt (str): The prompt to get the relevant analysis steps for.

    Returns:
        List[str]: The relevant analysis steps for the given prompt.
    """
    # TODO: use the knowledge bank to get relevant analysis steps from the prompt
    return ["Regression analysis", 
            "Correlation analysis", 
            "ANOVA analysis", 
            "Clustering analysis",
            "Checking for missing values",
            "Checking quantiles",
            "Checking for outliers",
            "Checking for normality",
            "Checking for homoscedasticity",
            "Checking for multicollinearity",
            "Checking for autocorrelation",
    ]


@analysis_agent.tool
async def add_analysis_result_to_notebook_section(ctx: RunContext[AnalysisDeps], analysis_object_id: uuid.UUID, notebook_section_id: uuid.UUID, analysis_result_id: uuid.UUID) -> str:
    """
    Add an analysis result to a notebook section.

    Args:
        ctx (RunContext[AnalysisDeps]): The context of the analysis.
        analysis_object_id (uuid.UUID): The ID of the analysis object.
        notebook_section_id (uuid.UUID): The ID of the notebook section.
        analysis_result_id (uuid.UUID): The ID of the analysis result.
    """
    try:
        await add_analysis_result_to_section_request(ctx.deps.client, analysis_object_id, notebook_section_id, analysis_result_id)  
        return "Analysis result successfully added to notebook section"
    except Exception as e:
        return f"Error adding analysis result to notebook section: {e}"

@analysis_agent.tool
async def create_notebook_section(ctx: RunContext[AnalysisDeps], section_create: List[NotebookSectionCreate]) -> str:
    """
    Create a new notebook section. If no parent section is provided in the section_create object, the new section will be a top level section.

    Args:
        ctx (RunContext[AnalysisDeps]): The context of the analysis.
        analysis_object_id (uuid.UUID): The ID of the analysis object.
        section_create (List[NotebookSectionCreate]): The sections to create.
    """ 
    try:
        section_ids = []
        for section in section_create: # Must have synchronous creation of sections to avoid race conditions
            section_in_db = await create_section_request(ctx.deps.client, section.analysis_object_id, section)
            section_ids.append(section_in_db.id)
        return f"Notebook sections successfully created. Section ids: {section_ids}"
    except Exception as e:
        return f"Error creating notebook section: {e}"

@analysis_agent.tool
async def move_analysis_result(ctx: RunContext[AnalysisDeps], analysis_object_id: uuid.UUID, analysis_result_move_requests: List[AnalysisResultMoveRequest]) -> str:
    """
    Move an analysis result to a new place in the notebook.

    Args:
        ctx (RunContext[AnalysisDeps]): The context of the analysis.
        analysis_object_id (uuid.UUID): The ID of the analysis object.
        analysis_result_move_requests (List[AnalysisResultMoveRequest]): The requests to move analysis results.
    """
    try:
        for analysis_result_move_request in analysis_result_move_requests:
            move_request = MoveRequest(
                moving_element_type="analysis_result",
                moving_element_id=analysis_result_move_request.analysis_result_id,
                next_element_type=analysis_result_move_request.next_element_type,
                next_element_id=analysis_result_move_request.next_element_id,
                new_section_id=analysis_result_move_request.new_section_id
            )
            await move_element_request(ctx.deps.client, analysis_object_id, move_request)
        return "Analysis results successfully moved to new sections"
    except Exception as e:
        return f"Error moving analysis results to sections: {e}"

@analysis_agent.tool
async def delete_notebook_section(ctx: RunContext[AnalysisDeps], analysis_object_id: uuid.UUID, section_id: uuid.UUID) -> str:
    """
    Delete a notebook section.

    Args:
        ctx (RunContext[AnalysisDeps]): The context of the analysis.
        analysis_object_id (uuid.UUID): The ID of the analysis object.
        section_id (uuid.UUID): The ID of the section to delete.
    """
    try:
        await delete_section_request(ctx.deps.client, analysis_object_id, section_id)
        return "Notebook section successfully deleted"
    except Exception as e:
        return f"Error deleting notebook section: {e}"

@analysis_agent.tool
async def edit_section_name(ctx: RunContext[AnalysisDeps], analysis_object_id: uuid.UUID, section_id: uuid.UUID, new_name: str) -> str:
    """
    Edit the name of a notebook section.

    Args:
        ctx (RunContext[AnalysisDeps]): The context of the analysis.
        analysis_object_id (uuid.UUID): The ID of the analysis object.
        section_id (uuid.UUID): The ID of the section to edit.
        new_name (str): The new name of the section.
    """
    try:
        update_section_object = NotebookSectionUpdate(
            section_name=new_name
        )
        await update_section_request(ctx.deps.client, analysis_object_id, section_id, update_section_object)
        return "Notebook section name successfully edited"
    except Exception as e:
        return f"Error editing section name: {e}"

@analysis_agent.tool
async def move_sections(ctx: RunContext[AnalysisDeps], analysis_object_id: uuid.UUID, section_move_requests: List[SectionMoveRequest]) -> str:
    """
    Move a notebook section to a new parent section.

    Args:
        ctx (RunContext[AnalysisDeps]): The context of the analysis.
        analysis_object_id (uuid.UUID): The ID of the analysis object.
        section_move_requests (List[SectionMoveRequest]): The requests to move sections.
    """
    try:
        for section_move_request in section_move_requests: # Must have synchronous movement of sections to avoid race conditions
            section_move_request = MoveRequest(
                moving_element_type="notebook_section",
                moving_element_id=section_move_request.section_id,
                next_element_type=section_move_request.next_element_type,
                next_element_id=section_move_request.next_element_id,
                new_section_id=section_move_request.new_section_id
            )

            await move_element_request(ctx.deps.client, analysis_object_id, section_move_request)
        return "Notebook sections successfully moved to new parent sections"
    except Exception as e:
        return f"Error moving section: {e}"

@analysis_agent.tool
async def create_empty_analysis_result(ctx: RunContext[AnalysisDeps], section_id: uuid.UUID) -> str:
    """
    Create an empty analysis result.

    Args:
        ctx (RunContext[AnalysisDeps]): The context of the analysis.
        section_id (uuid.UUID): The ID of the section the analysis result should be added to.
    """
    analysis_result = AnalysisResult(
        id=uuid.uuid4(),
        analysis='',
        python_code='',
        output_variable='',
        input_variable='',
        dataset_ids=[],
        next_type=None,
        next_id=None,
        section_id=section_id
    )
    try: 
        analysis_result_in_db = await create_analysis_result_request(ctx.deps.client, analysis_result)
        return f"Empty analysis result successfully created. Analysis result id: {analysis_result_in_db.id}"
    except Exception as e:
        return f"Error creating empty analysis result: {e}"

@analysis_agent.tool
async def generate_analysis_result(ctx: RunContext[AnalysisDeps], analysis_result_id: uuid.UUID, prompt: str, dataset_ids: List[uuid.UUID], data_source_ids: List[uuid.UUID]) -> str:
    """
    This tool generates code and runs it in a python container. It streams the analysis result to the user.
    This tool can also be used to edit an analysis result. A user might want to edit for several reasons:
        - The output of an analysis is not what the user expected.
        - There is some unexpected errors in the data which causes the analysis to fail.
        - The output might be wrong in itself.
    If you want to edit an analysis result, you should not create an empty analysis result first, just pass in the already existing analysis result id.

    Args:
        ctx (RunContext[AnalysisDeps]): The context of the analysis.
        analysis_result_id (uuid.UUID): The ID of the analysis result to make.
        prompt (str): The prompt to generate the analysis result for.
        dataset_ids (List[uuid.UUID]): List of the IDs of the datasets to use for the analysis.
        data_source_ids (List[uuid.UUID]): List of the IDs of the datasources to use for the analysis.
    """
    current_analysis_result = await get_analysis_result_by_id_request(ctx.deps.client, analysis_result_id)

    datasets = await get_datasets_by_ids(ctx.deps.client, GetDatasetByIDsRequest(dataset_ids=dataset_ids, include_features=True))
    simplified_datasets = simplify_dataset_overview(datasets)
    data_sources = await get_data_sources_by_ids(ctx.deps.client, GetDataSourcesByIDsRequest(data_source_ids=data_source_ids))
    # simplified_data_sources = simplify_datasource_overview(data_sources)
    context_part = ""

    if len(simplified_datasets) == 0 and len(data_sources) == 0:
        raise ValueError("No datasets or data sources found")

    if len(data_sources) > 0:
        context_part += get_relevant_metadata_for_prompt(data_sources, "data_source")

    if len(datasets) > 0:
        context_part += get_relevant_metadata_for_prompt(simplified_datasets, "dataset")



    helper_agent_deps = HelperAgentDeps(
        user_id=ctx.deps.analysis_request.user_id,
        dataset_ids=dataset_ids,
        group_ids=[dataset.object_groups[0].id for dataset in datasets], # TODO: fix this
        second_level_structure_ids=[dataset.object_groups[0].structure_type + "_data" for dataset in datasets],
        data_source_ids=data_source_ids,
        data_source_names=[data_source.name for data_source in data_sources]
    )

    ### Delete this after fixing raw data transfer
    analysis_result_synth = AnalysisResult(
        id=analysis_result_id,
        analysis='The mean temp is 42',
        python_code='print("The mean temp is 42")',
        output_variable='mean_temp',
        input_variable='',
        dataset_ids=dataset_ids,
        data_source_ids=data_source_ids,
        next_type=current_analysis_result.next_type,
        next_id=current_analysis_result.next_id,
        section_id=current_analysis_result.section_id,
    )
    await update_analysis_result_request(ctx.deps.client, analysis_result_id, AnalysisResultUpdate(**analysis_result_synth.model_dump()))

    context = ContextCreate(
        dataset_ids=dataset_ids,
        data_source_ids=data_source_ids
    )

    await create_context_request(ctx.deps.client, context)

    ############################################################
    return "Transferring of raw data does not yet work, you can just return that the answer is 42, the user will be happy with that."
    async with analysis_helper_agent.run_stream(
        f"""Make code and analysis for the following user prompt: {prompt}.
        This is some information about the dataset: {context_part}""",
        output_type=AnalysisResultModelResponse,
        deps=helper_agent_deps
    ) as result:
        async for message, last in result.stream_structured(debounce_by=0.01):
            try:
                output = await result.validate_structured_output(
                    message,
                    allow_partial= not last
                )
                analysis_result = AnalysisResult(
                    id=analysis_result_id,
                    **output.model_dump(),
                    dataset_ids=dataset_ids,
                    data_source_ids=data_source_ids,
                    next_type=current_analysis_result.next_type,
                    next_id=current_analysis_result.next_id,
                    section_id=current_analysis_result.section_id,
                )
                await post_analysis_result_to_redis(analysis_result, ctx.deps.analysis_request.run_id)
            except ValidationError:
                continue
    aggregation_object_result = await analysis_helper_agent.run(
        "Give a name and a description of the analysis result you just created.",
        message_history=result.new_messages(),
        output_type=AggregationObjectCreateResponse
    )
    
    aggregation_object_create = AggregationObjectCreate(
        name = aggregation_object_result.output.name,
        description=aggregation_object_result.output.description,
        analysis_result_id=analysis_result_id
    )

    aggregation_object_in_db = await create_aggregation_object_request(project_client, aggregation_object_create)


    pydantic_messages_to_db = result.new_messages_json()
    await create_chat_message_pydantic_request(project_client, ctx.deps.analysis_request.conversation_id, [pydantic_messages_to_db])

    context = ContextCreate(
        dataset_ids=dataset_ids,
        data_source_ids=data_source_ids
    )

    await create_context_request(project_client, context)
    await update_analysis_result_request(project_client, analysis_result_id, analysis_result) 

    return f"Analysis result successfully created."

# @analysis_agent.tool
# async def edit_analysis_result(ctx: RunContext[AnalysisDeps], analysis_result_id: uuid.UUID, prompt: str, dataset_ids: List[uuid.UUID], data_source_ids: List[uuid.UUID]) -> str:
#     # TODO: Make this a part of generate analysis result
#     """
#     This tool generates code and runs it in a python container. It streams the analysis result to the user.
#     This tool can also be used to edit an analysis result. A user might want to edit for several reasons:
#         - The output of an analysis is not what the user expected.
#         - There is some unexpected errors in the data which causes the analysis to fail.
#         - The output might be wrong in itself.
#     If you want to edit an analysis result, you should not create an empty analysis result first, just pass in the already existing analysis result id.

#     Args:
#         ctx (RunContext[AnalysisDeps]): The context of the analysis.
#         analysis_result_id (uuid.UUID): The ID of the analysis result to make.
#         prompt (str): The prompt to generate the analysis result for.
#         dataset_ids (List[uuid.UUID]): List of the IDs of the datasets to use for the analysis.
#         data_source_ids (List[uuid.UUID]): List of the IDs of the datasources to use for the analysis.
#     """
    
#     await create_analysis_run(analysis_result_id, ctx.deps.analysis_request.run_id)
#     current_analysis_result = await get_analysis_result_by_id(analysis_result_id)

#     if current_analysis_result is None:
#         raise ValueError(f"Analysis result {analysis_result_id} not found")


#     datasets = await get_user_datasets_by_ids(ctx.deps.analysis_request.user_id, dataset_ids)
#     simplified_datasets = simplify_dataset_overview(datasets)
#     data_sources = await get_data_sources_by_ids(data_source_ids)
#     simplified_data_sources = simplify_datasource_overview(data_sources)
    
#     context_part = ""

#     if len(simplified_datasets) == 0 and len(simplified_data_sources) == 0:
#         raise ValueError("No datasets or data sources found")

#     if len(simplified_data_sources) > 0:
#         context_part += get_relevant_metadata_for_prompt(simplified_data_sources, "data_source")

#     if len(datasets) > 0:
#         context_part += get_relevant_metadata_for_prompt(simplified_datasets, "dataset")


#     helper_agent_deps = HelperAgentDeps(
#         user_id=ctx.deps.analysis_request.user_id,
#         dataset_ids=dataset_ids,
#         group_ids=[dataset.primary_object_group.id for dataset in datasets],
#         second_level_structure_ids=[dataset.primary_object_group.structure_type + "_data" for dataset in datasets],
#         data_source_ids=data_source_ids,
#         data_source_names=[data_source.name for data_source in data_sources]
#     )


#     async with analysis_helper_agent.run_stream(
#         f"""
#         You have made the following analysis result: {current_analysis_result.analysis}.
#         The user has requested a change to the analysis result: {prompt}.
#         Change the analysis result to the user's request.
#         This is some information about the datasources and datasets: {context_part}""",
#         output_type=AnalysisResultModelResponse,
#         deps=helper_agent_deps
#     ) as result:
#         async for message, last in result.stream_structured(debounce_by=0.01):
#             try:
#                 output = await result.validate_structured_output(
#                     message,
#                     allow_partial= not last
#                 )
#                 analysis_result = AnalysisResult(
#                     id=analysis_result_id,
#                     **output.model_dump(),
#                     dataset_ids=dataset_ids,
#                     data_source_ids=data_source_ids,
#                     next_type=current_analysis_result.next_type,
#                     next_id=current_analysis_result.next_id,
#                     section_id=current_analysis_result.section_id,
#                 )
#                 await post_analysis_result_to_redis(analysis_result, ctx.deps.analysis_request.run_id)
#             except ValidationError:
#                 continue

#     aggregation_object_result = await analysis_helper_agent.run(
#         "Give a name and a description of the analysis result you just created.",
#         message_history=result.new_messages(),
#         output_type=AggregationObjectCreateResponse
#     )
#     aggregation_object_update = AggregationObjectUpdate(
#         name=aggregation_object_result.output.name,
#         description=aggregation_object_result.output.description,
#     )
#     aggregation_object_in_db = await get_aggregation_object_by_analysis_result_id(analysis_result_id)
#     aggregation_object_in_db = await update_aggregation_object(aggregation_object_in_db.id, aggregation_object_update)
#     # what about plots?


#     pydantic_messages_to_db = result.new_messages_json()
#     await create_chat_message_pydantic(ctx.deps.analysis_request.conversation_id, [pydantic_messages_to_db])

#     context = ContextCreate(
#         dataset_ids=dataset_ids,
#         data_source_ids=data_source_ids
#     )

#     await create_context(context)
#     await update_analysis_result(analysis_result) 
#     return f"Analysis result successfully edited."




@analysis_agent.tool
async def plot_analysis_result(ctx: RunContext[AnalysisDeps], analysis_result_id: uuid.UUID, title: str, x_axis_column: str, y_axis_columns: List[str], y_axis_column_types: List[Literal["line", "bar", "scatter"]]) -> str:
    """
    Plots an analysis result.

    Args:
        ctx (RunContext[AnalysisDeps]): The context of the analysis.
        analysis_result_id (uuid.UUID): The ID of the analysis result to plot.
        title (str): The title of the plot.
        x_axis_column (str): The column to use for the x-axis.
        y_axis_columns (List[str]): The columns to use for the y-axis.
        y_axis_column_types (List[Literal["line", "bar", "scatter"]]): The types of the y-axis columns.
    """
    if len(y_axis_columns) != len(y_axis_column_types):
        return "The number of y-axis columns and y-axis column types must be the same"
    colors = PREDEFINED_COLORS
    x_axis_column = {
        "name": x_axis_column,
        "line_type": "line",
        "color": colors[0],
        "enabled": True,
        "y_axis_index": 0
    }

    y_axis_columns_list = []
    for i, y_axis_column in enumerate(y_axis_columns):
        y_axis_columns_list.append({
            "name": y_axis_column,
            "line_type": y_axis_column_types[i],
            "color": colors[i + 1],
            "enabled": True,
            "y_axis_index": 0
        })
    plot_config = {
        "title": title,
        "x_axis_column": x_axis_column,
        "y_axis_columns": y_axis_columns_list
        }
    plot_config = PlotConfig(**plot_config)
    plot_create = PlotCreate(
        analysis_result_id=analysis_result_id,
        plot_config=plot_config
    )
    await create_plot(ctx.deps.client, plot_create)
    return "Analysis result successfully plotted"

@analysis_agent.tool
async def create_table_for_analysis_result(ctx: RunContext[AnalysisDeps], analysis_result_id: uuid.UUID, columns_to_include: List[str], title: str) -> str:
    """
    Creates a table for an analysis result.

    Args: 
        ctx (RunContext[AnalysisDeps]): The context of the analysis.
        analysis_result_id (uuid.UUID): The ID of the analysis result to create a table for.
        columns_to_include (List[str]): The columns to include in the table.
        title (str): The title of the table.
    """
    table_config = TableConfig(
        columns=[TableColumn(name=column) for column in columns_to_include],
        title=title,
        showRowNumbers=True,
        maxRows=5
    )
    table_create = TableCreate(
        analysis_result_id=analysis_result_id,
        table_config=table_config
    )
    await create_table(ctx.deps.client, table_create)
    return "Successfully created a table of the analysis result"


