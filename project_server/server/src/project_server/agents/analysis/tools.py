import uuid
from pathlib import Path
from pydantic import ValidationError
from pydantic_ai import RunContext
from typing import List, Optional
from datetime import datetime

from project_server.worker import logger
from synesis_schemas.main_server import (
    AnalysisResult,
    NotebookSectionCreate,
    MoveRequest,
    NotebookSectionUpdate,
    AnalysisStatusMessage,
    EchartCreate,
    TableCreate,
    ImageCreate,
    AnalysisResultVisualizationCreate,
)
from project_server.agents.analysis.utils import post_update_to_redis
from project_server.client import (
    create_section_request,
    update_section_request,
    delete_section_request,
    # add_analysis_result_to_section_request,
    move_element_request,
    update_analysis_result_request,
    create_analysis_result_request,
    get_analysis_result_by_id_request,
    create_analysis_result_visualization_request,
)
from project_server.utils.docker_utils import copy_file_from_container
from project_server.agents.analysis.helper_agent import analysis_helper_agent, HelperAgentDeps
from project_server.agents.analysis.deps import AnalysisDeps
from project_server.agents.analysis.output import AnalysisResultMoveRequest, SectionMoveRequest
from project_server.app_secrets import AGENT_OUTPUTS_INTERNAL_HOST_DIR


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
            analysis_status_message = AnalysisStatusMessage(
                id=uuid.uuid4(),
                run_id=ctx.deps.run_id,
                section=section_in_db,
                created_at=datetime.now()
            )

            await post_update_to_redis(analysis_status_message, ctx.deps.run_id)
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
            next_type=None,
            next_id=None,
            section_id=section_id
        )
        analysis_result_in_db = await create_analysis_result_request(ctx.deps.client, current_analysis_result)
        analysis_result_id = analysis_result_in_db.id
    else:
        current_analysis_result = await get_analysis_result_by_id_request(ctx.deps.client, analysis_result_id)

    analysis_status_message = AnalysisStatusMessage(
        id=uuid.uuid4(),
        run_id=ctx.deps.run_id,
        analysis_result=current_analysis_result,
        created_at=datetime.now()
    )
    await post_update_to_redis(analysis_status_message, ctx.deps.run_id)

    helper_agent_deps = HelperAgentDeps(
        client=ctx.deps.client,
        container_name=ctx.deps.container_name,
        model_instantiatedies_injected=ctx.deps.model_instantiatedies_injected,
        data_sources_injected=ctx.deps.data_sources_injected,
        datasets_injected=ctx.deps.datasets_injected,
        analysis_id=ctx.deps.analysis_id,
        analysis_result_id=analysis_result_id,
        project_id=ctx.deps.project_id,
    )

    async with analysis_helper_agent.run_stream(
        f"You will now create some code and analysis for the user. Generate code and analysis for the following user prompt: {prompt}. \n\n",
        deps=helper_agent_deps,
        # message_history=ctx.deps.helper_history
    ) as result:
        async for message, last in result.stream_responses(debounce_by=0.01):
            try:
                output = await result.validate_response_output(
                    message,
                    allow_partial=not last
                )
                analysis_result = AnalysisResult(
                    id=analysis_result_id,
                    **output.model_dump(),
                    next_type=current_analysis_result.next_type,
                    next_id=current_analysis_result.next_id,
                    section_id=current_analysis_result.section_id,
                    # I guess we assume only one code run? Even though it can be multiple?
                    python_code=output.code,
                    image_ids=[image.id for image in output.images],
                    echart_ids=[echart.id for echart in output.charts],
                    table_ids=[table.id for table in output.tables],
                )
                analysis_status_message = AnalysisStatusMessage(
                    id=uuid.uuid4(),
                    run_id=ctx.deps.run_id,
                    analysis_result=analysis_result,
                    created_at=datetime.now()
                )
                await post_update_to_redis(analysis_status_message, ctx.deps.run_id)
            except ValidationError:
                continue

    await update_analysis_result_request(ctx.deps.client, analysis_result)

    ctx.deps.helper_history += result.new_messages()

    return_string = (
        f"Analysis result successfully created. Analysis result id: {analysis_result.id}\n"
        f"This is the output of the analysis: {output}\n"
    )

    ctx.deps.results_generated = True
    return return_string
