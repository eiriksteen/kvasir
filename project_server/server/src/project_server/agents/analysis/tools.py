import uuid
from pydantic import ValidationError
from pydantic_ai import RunContext
from typing import List, Literal, Optional


from synesis_schemas.main_server import (
    AnalysisResult,
    NotebookSectionCreate,
    MoveRequest,
    NotebookSectionUpdate,
    AnalysisResultFindRequest,
    PlotCreate,
    PREDEFINED_COLORS,
    PlotConfig,
    TableCreate,
    TableConfig,
    TableColumn,
    AggregationObjectCreate,
)
from project_server.agents.analysis.utils import post_analysis_result_to_redis
from project_server.client import (
    create_section_request,
    update_section_request,
    delete_section_request,
    add_analysis_result_to_section_request,
    move_element_request,
    update_analysis_result_request,
    create_analysis_result_request,
    get_analysis_result_by_id_request,
    get_analysis_results_by_ids_request,
    create_aggregation_object_request,
)
from project_server.client.requests.plots import create_plot
from project_server.client.requests.tables import create_table
from project_server.agents.analysis.helper_agent import analysis_helper_agent, HelperAgentDeps
from project_server.agents.analysis.deps import AnalysisDeps
from project_server.agents.analysis.output import AnalysisResultModelResponse, AggregationObjectCreateResponse, AnalysisResultMoveRequest, SectionMoveRequest
from project_server.app_secrets import ANALYSIS_DIR


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


async def add_analysis_result_to_notebook_section(ctx: RunContext[AnalysisDeps], notebook_section_id: uuid.UUID, analysis_result_id: uuid.UUID) -> str:
    """
    Add an analysis result to a notebook section.

    Args:
        ctx (RunContext[AnalysisDeps]): The context of the analysis.
        notebook_section_id (uuid.UUID): The ID of the notebook section.
        analysis_result_id (uuid.UUID): The ID of the analysis result.
    """
    try:
        await add_analysis_result_to_section_request(ctx.deps.client, ctx.deps.analysis_id, notebook_section_id, analysis_result_id)
        return "Analysis result successfully added to notebook section"
    except Exception as e:
        return f"Error adding analysis result to notebook section: {e}"


async def create_notebook_section(ctx: RunContext[AnalysisDeps], section_create: List[NotebookSectionCreate]) -> str:
    """
    Create a new notebook section. If no parent section is provided in the section_create object, the new section will be a top level section.

    Args:
        ctx (RunContext[AnalysisDeps]): The context of the analysis.
        section_create (List[NotebookSectionCreate]): The sections to create.
    """
    try:
        section_ids = []
        for section in section_create:  # Must have synchronous creation of sections to avoid race conditions
            section_in_db = await create_section_request(ctx.deps.client, ctx.deps.analysis_id, section)
            section_ids.append(section_in_db.id)
        return f"Notebook sections successfully created. Section ids: {section_ids}"
    except Exception as e:
        return f"Error creating notebook section: {e}"


async def move_analysis_result(ctx: RunContext[AnalysisDeps], analysis_result_move_requests: List[AnalysisResultMoveRequest]) -> str:
    """
    Move an analysis result to a new place in the notebook.

    Args:
        ctx (RunContext[AnalysisDeps]): The context of the analysis.
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
            await move_element_request(ctx.deps.client, ctx.deps.analysis_id, move_request)
        return "Analysis results successfully moved to new sections"
    except Exception as e:
        return f"Error moving analysis results to sections: {e}"


async def delete_notebook_section(ctx: RunContext[AnalysisDeps], section_id: uuid.UUID) -> str:
    """
    Delete a notebook section.

    Args:
        ctx (RunContext[AnalysisDeps]): The context of the analysis.
        section_id (uuid.UUID): The ID of the section to delete.
    """
    try:
        await delete_section_request(ctx.deps.client, ctx.deps.analysis_id, section_id)
        return "Notebook section successfully deleted"
    except Exception as e:
        return f"Error deleting notebook section: {e}"


async def edit_section_name(ctx: RunContext[AnalysisDeps], section_id: uuid.UUID, new_name: str) -> str:
    """
    Edit the name of a notebook section.

    Args:
        ctx (RunContext[AnalysisDeps]): The context of the analysis.
        section_id (uuid.UUID): The ID of the section to edit.
        new_name (str): The new name of the section.
    """
    try:
        update_section_object = NotebookSectionUpdate(
            section_name=new_name
        )
        await update_section_request(ctx.deps.client, ctx.deps.analysis_id, section_id, update_section_object)
        return "Notebook section name successfully edited"
    except Exception as e:
        return f"Error editing section name: {e}"


async def move_sections(ctx: RunContext[AnalysisDeps], section_move_requests: List[SectionMoveRequest]) -> str:
    """
    Move a notebook section to a new parent section.

    Args:
        ctx (RunContext[AnalysisDeps]): The context of the analysis.
        section_move_requests (List[SectionMoveRequest]): The requests to move sections.
    """
    try:
        # Must have synchronous movement of sections to avoid race conditions
        for section_move_request in section_move_requests:
            section_move_request = MoveRequest(
                moving_element_type="notebook_section",
                moving_element_id=section_move_request.section_id,
                next_element_type=section_move_request.next_element_type,
                next_element_id=section_move_request.next_element_id,
                new_section_id=section_move_request.new_section_id
            )

            await move_element_request(ctx.deps.client, ctx.deps.analysis_id, section_move_request)
        return "Notebook sections successfully moved to new parent sections"
    except Exception as e:
        return f"Error moving section: {e}"


# async def create_empty_analysis_result(ctx: RunContext[AnalysisDeps], section_id: uuid.UUID) -> str:
#     """
#     Create an empty analysis result.

#     Args:
#         ctx (RunContext[AnalysisDeps]): The context of the analysis.
#         section_id (uuid.UUID): The ID of the section the analysis result should be added to.
#     """
#     analysis_result = AnalysisResult(
#         id=uuid.uuid4(),
#         analysis='',
#         python_code='',
#         output_variable='',
#         input_variable='',
#         dataset_ids=[],
#         next_type=None,
#         next_id=None,
#         section_id=section_id
#     )
#     try:
#         analysis_result_in_db = await create_analysis_result_request(ctx.deps.client, analysis_result)
#         return f"Empty analysis result successfully created. Analysis result id: {analysis_result_in_db.id}"
#     except Exception as e:
#         return f"Error creating empty analysis result: {e}"


async def generate_analysis_result(
    ctx: RunContext[AnalysisDeps],
    prompt: str,
    dataset_ids: List[uuid.UUID],
    data_source_ids: List[uuid.UUID],
    analysis_result_id: Optional[uuid.UUID] = None,
    section_id: Optional[uuid.UUID] = None,
) -> str:
    """
    This tool generates code and runs it in a python container. It streams the analysis result to the user.
    This tool can also be used to edit an analysis result. A user might want to edit for several reasons:
        - The output of an analysis is not what the user expected.
        - There is some unexpected errors in the data which causes the analysis to fail.
        - The output might be wrong in itself.
    If you want to edit an analysis result, you should not create an empty analysis result first, just pass in the already existing analysis result id.

    Args:
        ctx (RunContext[AnalysisDeps]): The context of the analysis.
        prompt (str): The prompt to generate the analysis result for. 
        dataset_ids (List[uuid.UUID]): List of the IDs of the datasets to use for the analysis.
        data_source_ids (List[uuid.UUID]): List of the IDs of the datasources to use for the analysis.
        analysis_result_id (Optional[uuid.UUID]): The ID of the analysis result to edit. If not provided, a new analysis result will be created.
        section_id (Optional[uuid.UUID]): The ID of the section to add the analysis result to. Required if analysis result ID is not provided. Not used if analysis result ID is provided.
    """

    if analysis_result_id is None:
        assert section_id is not None, "Section ID is required if analysis result ID is not provided"
        current_analysis_result = AnalysisResult(
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
        analysis_result_in_db = await create_analysis_result_request(ctx.deps.client, current_analysis_result)
        analysis_result_id = analysis_result_in_db.id
    else:
        current_analysis_result = await get_analysis_result_by_id_request(ctx.deps.client, analysis_result_id)

    helper_agent_deps = HelperAgentDeps(
        model_entities_injected=ctx.deps.model_entities_injected,
        data_sources_injected=ctx.deps.data_sources_injected,
        datasets_injected=ctx.deps.datasets_injected,
        analysis_id=ctx.deps.analysis_id,
        analysis_result_id=analysis_result_id,
        bearer_token=ctx.deps.client.bearer_token,
    )

    plot_path = ANALYSIS_DIR / \
        str(ctx.deps.analysis_id) / str(analysis_result_id) / "plots"
    plot_path.mkdir(parents=True, exist_ok=True)

    async with analysis_helper_agent.run_stream(
        f"You will now create some code and analysis for the user. Generate code and analysis for the following user prompt: {prompt}. \n\n",
        output_type=AnalysisResultModelResponse,
        deps=helper_agent_deps
    ) as result:
        async for message, last in result.stream_structured(debounce_by=0.01):
            try:
                output = await result.validate_structured_output(
                    message,
                    allow_partial=not last
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
                await post_analysis_result_to_redis(analysis_result, ctx.deps.run_id)
            except ValidationError:
                continue

    aggregation_object_result = await analysis_helper_agent.run(
        "Give a name and a description of the analysis result you just created.",
        message_history=result.new_messages(),
        output_type=AggregationObjectCreateResponse
    )

    aggregation_object_create = AggregationObjectCreate(
        name=aggregation_object_result.output.name,
        description=aggregation_object_result.output.description,
        analysis_result_id=analysis_result_id
    )

    await create_aggregation_object_request(ctx.deps.client, aggregation_object_create)

    plot_files = []
    plot_dir = ANALYSIS_DIR / \
        str(ctx.deps.analysis_id) / str(analysis_result_id) / "plots"
    if plot_dir.exists():
        plot_files = [str(p.name) for p in plot_dir.glob("*.png")]

    analysis_result.plot_urls = plot_files

    await update_analysis_result_request(ctx.deps.client, analysis_result)
    return_string = f"""
        Analysis result successfully created. Analysis result id: {analysis_result.id}
        This is the outcome of the analysis: {analysis_result.analysis}
        This is the python code that was used to generate the analysis result: {analysis_result.python_code}
    """

    ctx.deps.results_generated = True
    return return_string


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
