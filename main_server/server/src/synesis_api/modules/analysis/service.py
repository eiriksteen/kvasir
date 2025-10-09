import uuid
import numpy as np
from datetime import datetime
from fastapi import HTTPException
from sqlalchemy import update, select, insert, delete, and_
from typing import List, Tuple, Literal
from synesis_api.database.service import execute, fetch_one, fetch_all
from synesis_api.modules.analysis.models import (
    analysis_objects, 
    analysis_objects_datasets, 
    analysis_results, 
    analysis_results_datasets,
    notebook_sections,
    notebooks,
    analysis_result_runs,
    analysis_results_data_sources,
)
from synesis_api.modules.orchestrator.models import analysis_context
from synesis_api.modules.plots.models import plots
from synesis_api.modules.tables.models import tables
from synesis_schemas.main_server import (
    AnalysisObject, 
    AnalysisObjectCreate, 
    AnalysisObjectInDB, 
    AnalysisResult,
    AnalysisResultInDB,
    NotebookSectionCreate,
    NotebookSectionInDB,
    NotebookInDB,
    AnalysisObjectSmall,
    Notebook,
    NotebookSection,
    AnalysisObjectList,
    MoveRequest,
    NotebookSectionUpdate,
    AnalysisResultUpdate
)
from synesis_api.modules.node.service import delete_node
from synesis_api.modules.project.service import remove_entity_from_project
from synesis_schemas.main_server import RemoveEntityFromProject
from synesis_api.modules.analysis.utils import deep_exclude

async def create_analysis_object(analysis_object_create: AnalysisObjectCreate, user_id: uuid.UUID) -> AnalysisObjectInDB:

    analysis_object_id = uuid.uuid4()
    notebook = await create_notebook()

    analysis_object = AnalysisObjectInDB(
        id=analysis_object_id,
        user_id=user_id,
        notebook_id=notebook.id,
        **analysis_object_create.model_dump(),
    )

    await execute(
        insert(analysis_objects).values(
            **analysis_object.model_dump(exclude={"dataset_ids"})
        ),
        commit_after=True
    )

    return analysis_object

async def get_analysis_object_by_id(analysis_object_id: uuid.UUID) -> AnalysisObject:
    result = await fetch_one(
        select(analysis_objects).where(analysis_objects.c.id == analysis_object_id)
    )
    if result is None:
        raise HTTPException(
            status_code=404, detail="Analysis object not found"
        )
    
    notebook = await get_notebook_by_id(result["notebook_id"])

    return AnalysisObject(**result, notebook=notebook)


async def get_analysis_objects_small_by_project_id(project_id: uuid.UUID) -> AnalysisObjectList:
    results = await fetch_all(
        select(analysis_objects).where(analysis_objects.c.project_id == project_id)
    )
    
    analysis_objects_list = []
    for result in results:
        analysis_objects_list.append(AnalysisObjectSmall(**result))
    
    return AnalysisObjectList(analysis_objects=analysis_objects_list)


async def get_user_analysis_objects_by_ids(user_id: uuid.UUID, analysis_ids: List[uuid.UUID]) -> List[AnalysisObject]:
    results = await fetch_all(
        select(analysis_objects).where(
            analysis_objects.c.user_id == user_id,
            analysis_objects.c.id.in_(analysis_ids)
        )
    )
    
    analysis_objects_list = []
    for result in results:
        notebook = await get_notebook_by_id(result["notebook_id"])
        analysis_objects_list.append(AnalysisObject(**result, notebook=notebook))
    
    return analysis_objects_list

async def get_simplified_overview_for_context_message(user_id: uuid.UUID, analysis_ids: list[uuid.UUID]) -> str:
    analysis_objects = await get_user_analysis_objects_by_ids(user_id, analysis_ids)
    simplified_overview = [deep_exclude(analysis_object.model_dump(), set(["analysis", "python_code", "input_variable"])) for analysis_object in analysis_objects]
    return simplified_overview


async def delete_analysis_object(analysis_object_id: uuid.UUID, node_id: uuid.UUID, user_id: uuid.UUID) -> uuid.UUID:
    # Get the analysis object to access user_id
    analysis_object = await get_analysis_object_by_id(analysis_object_id)

    # Delete all sections and their mappings
    sections_to_delete = await fetch_all(
        select(notebook_sections).where(
            notebook_sections.c.notebook_id == analysis_object.notebook.id,
            notebook_sections.c.parent_section_id == None
        )
    )
    
    section_ids = [section["id"] for section in sections_to_delete]
    
    for section_id in section_ids:
        await delete_notebook_section_recursive(section_id)
    
    # Delete from analysis_objects_datasets
    # await execute(
    #     delete(analysis_objects_datasets).where(analysis_objects_datasets.c.analysis_object_id == analysis_object_id),
    #     commit_after=True
    # )
    
    # Delete node
    await delete_node(node_id)

    # Delete from project_analysis
    await remove_entity_from_project(analysis_object.project_id, RemoveEntityFromProject(entity_type="analysis", entity_id=analysis_object_id))

    # Delete from analysis context
    await execute(
        delete(analysis_context).where(analysis_context.c.analysis_id == analysis_object_id),
        commit_after=True
    )
    
    # Delete the notebook
    await execute(
        delete(notebooks).where(notebooks.c.id == analysis_object.notebook.id),
        commit_after=True
    )
    
    # Delete from analysis_objects
    await execute(
        delete(analysis_objects).where(analysis_objects.c.id == analysis_object_id),
        commit_after=True
    )
    
    return analysis_object_id


# TODO: Decide what to do with this function
async def add_dataset_to_analysis_object(analysis_object_id: uuid.UUID, dataset_id: uuid.UUID) -> None:
    await execute(
        insert(analysis_objects_datasets).values(
            analysis_object_id=analysis_object_id,
            dataset_id=dataset_id
        ),
        commit_after=True
    )

# TODO: Decide what to do with this function
async def remove_dataset_from_analysis_object(analysis_object_id: uuid.UUID, dataset_id: uuid.UUID) -> None:
    await execute(
        delete(analysis_objects_datasets).where(
            analysis_objects_datasets.c.analysis_object_id == analysis_object_id,
            analysis_objects_datasets.c.dataset_id == dataset_id
        ),
        commit_after=True
    )


async def create_analysis_result(analysis_result: AnalysisResult) -> AnalysisResultInDB:
    last_type, last_id = await get_last_element_in_section(analysis_result.section_id)
    if last_type == "analysis_result":
        await execute(
            update(analysis_results).where(analysis_results.c.id == last_id).values(
                next_type="analysis_result",
                next_id=analysis_result.id
            ),
            commit_after=True
        )
    elif last_type == "notebook_section":
        await execute(
            update(notebook_sections).where(notebook_sections.c.id == last_id).values(
                next_type="analysis_result",
                next_id=analysis_result.id
            ),
            commit_after=True
        )
    analysis_result_in_db = AnalysisResultInDB(
        **analysis_result.model_dump()
    )

    await execute(
        insert(analysis_results).values(
            **analysis_result_in_db.model_dump()
        ),
        commit_after=True
    )

    # Add dataset mappings
    if analysis_result.dataset_ids:
        for dataset_id in analysis_result.dataset_ids:
            await execute(
                insert(analysis_results_datasets).values(
                    analysis_result_id=analysis_result_in_db.id,
                    dataset_id=dataset_id
                ),
                commit_after=True
            )
    
    # Add datasource mappings
    if analysis_result.data_source_ids:
        for data_source_id in analysis_result.data_source_ids:
            await execute(
                insert(analysis_results_data_sources).values(
                    analysis_result_id=analysis_result_in_db.id,
                    data_source_id=data_source_id
                ),
                commit_after=True
            )

    return analysis_result_in_db

async def get_last_element_in_section(section_id: uuid.UUID, notebook_id: uuid.UUID | None = None) -> Tuple[Literal['analysis_result', 'notebook_section'], uuid.UUID] | Tuple[None, None]:
    """
    Gets all the analysis results and notebook sections in the given section and returns the type of the element and the 
    id of the element which does not have a next element.
    """
    result = await fetch_one(
        select(analysis_results).where(and_(analysis_results.c.section_id == section_id, analysis_results.c.next_id == None))
    )
    if result:
        return "analysis_result", result["id"]
    # Only need the notebook_id if we are getting the last element in a section that is a root section (no parent section) otherwise it may get a section from a different analysis object/notebook
    result = await fetch_one(
        select(notebook_sections).where(and_(notebook_sections.c.parent_section_id == section_id, notebook_sections.c.next_id == None, notebook_sections.c.notebook_id == notebook_id))
    )
    if result:
        return "notebook_section", result["id"]
    return None, None


async def add_analysis_result_to_section(section_id: uuid.UUID, analysis_result_id: uuid.UUID) -> NotebookSectionInDB:
    prev_type, prev_id = await get_last_element_in_section(section_id)

    if prev_type == "analysis_result":
        await execute(
            update(analysis_results).where(analysis_results.c.id == prev_id).values(
                next_type="analysis_result",
                next_id=analysis_result_id
            ),
            commit_after=True
        )
    elif prev_type == "notebook_section":
        await execute(
            update(notebook_sections).where(notebook_sections.c.id == prev_id).values(
                next_type="analysis_result",
                next_id=analysis_result_id
            ),
            commit_after=True
        )

    await execute(
        update(analysis_results).where(analysis_results.c.id == analysis_result_id).values(
            section_id=section_id
        ),
        commit_after=True
    )
    return await get_notebook_section_by_id(section_id)


async def get_data_source_ids_by_analysis_result_id(analysis_result_id: uuid.UUID) -> List[uuid.UUID]:
    data_source_mappings = await fetch_all(
        select(analysis_results_data_sources).where(analysis_results_data_sources.c.analysis_result_id == analysis_result_id)
    )
    return [mapping["data_source_id"] for mapping in data_source_mappings]


async def get_dataset_ids_by_analysis_result_id(analysis_result_id: uuid.UUID) -> List[uuid.UUID]:
    dataset_mappings = await fetch_all(
        select(analysis_results_datasets).where(analysis_results_datasets.c.analysis_result_id == analysis_result_id)
    )
    
    return [mapping["dataset_id"] for mapping in dataset_mappings]


async def check_user_owns_analysis_object(user_id: uuid.UUID, analysis_object_id: uuid.UUID) -> bool:
    result = await fetch_one(
        select(analysis_objects).where(
            analysis_objects.c.id == analysis_object_id,
            analysis_objects.c.user_id == user_id
        )
    )
    return result is not None


async def create_analysis_run(analysis_result_id: uuid.UUID, run_id: uuid.UUID) -> None:
    await execute(
        insert(analysis_result_runs).values(
            analysis_result_id=analysis_result_id,
            run_id=run_id
        ),
        commit_after=True
    )


async def create_section(notebook_section_create: NotebookSectionCreate) -> NotebookSectionInDB:
    analysis_object = await fetch_one(
        select(analysis_objects).where(analysis_objects.c.id == notebook_section_create.analysis_object_id)
    )
    last_type, last_id = await get_last_element_in_section(notebook_section_create.parent_section_id, analysis_object["notebook_id"])

    notebook_section = NotebookSectionInDB(
        id=uuid.uuid4(),
        **notebook_section_create.model_dump(),
        notebook_id=analysis_object["notebook_id"]
    )
    await execute(
        insert(notebook_sections).values(
            **notebook_section.model_dump()
        ),
        commit_after=True
    )


    if last_type == "analysis_result":
        await execute(
            update(analysis_results).where(analysis_results.c.id == last_id).values(
                next_type="notebook_section",
                next_id=notebook_section.id
            ),
            commit_after=True
        )
    elif last_type == "notebook_section":
        await execute(
            update(notebook_sections).where(notebook_sections.c.id == last_id).values(
                next_type="notebook_section",
                next_id=notebook_section.id
            ),
            commit_after=True
        )
    return notebook_section


async def get_notebook_section_by_id(section_id: uuid.UUID) -> NotebookSectionInDB:
    result = await fetch_one(
        select(notebook_sections).where(notebook_sections.c.id == section_id)
    )
    return NotebookSectionInDB(**result)


async def delete_analysis_result(analysis_result_id: uuid.UUID) -> None:
    current_analysis_result = await get_analysis_result_by_id(analysis_result_id)
    previous_type, previous_id = await get_prev_element(analysis_result_id, "analysis_result", current_analysis_result.section_id)
    if previous_type == "analysis_result":
        await execute(
            update(analysis_results).where(analysis_results.c.id == previous_id).values(
                next_type=current_analysis_result.next_type,
                next_id=current_analysis_result.next_id,
            ),
            commit_after=True
        )
    elif previous_type == "notebook_section":
        await execute(
            update(notebook_sections).where(notebook_sections.c.id == previous_id).values(
                next_type=current_analysis_result.next_type,
                next_id=current_analysis_result.next_id,
            ),
            commit_after=True
        )
    await execute(
        delete(analysis_results_datasets).where(analysis_results_datasets.c.analysis_result_id == analysis_result_id),
        commit_after=True
    )
    await execute(
        delete(analysis_results_data_sources).where(analysis_results_data_sources.c.analysis_result_id == analysis_result_id),
        commit_after=True
    )
    await execute(
        delete(analysis_result_runs).where(analysis_result_runs.c.analysis_result_id == analysis_result_id),
        commit_after=True
    )
    await execute(
        delete(plots).where(plots.c.analysis_result_id == analysis_result_id),
        commit_after=True
    )
    await execute(
        delete(tables).where(tables.c.analysis_result_id == analysis_result_id),
        commit_after=True
    )
    
    await execute(
        delete(analysis_results).where(analysis_results.c.id == analysis_result_id),
        commit_after=True
    )

async def delete_notebook_section(section_id: uuid.UUID) -> None:
    # Delete associated analysis results first due to foreign key constraints
    analysis_results_for_section = await get_analysis_results_by_section_id(section_id)
    for analysis_result in analysis_results_for_section:
        await delete_analysis_result(analysis_result.id)
    
    # Then delete the section itself
    section = await get_notebook_section_by_id(section_id)
    last_type, last_id = await get_prev_element(section.id, "notebook_section", section.parent_section_id)
    print("last_type", last_type)
    print("last_id", last_id)
    if last_type == "analysis_result":
        await execute(
            update(analysis_results).where(analysis_results.c.id == last_id).values(
                next_type=section.next_type,
                next_id=section.next_id,
            ),
            commit_after=True
        )
    elif last_type == "notebook_section":
        await execute(
            update(notebook_sections).where(notebook_sections.c.id == last_id).values(
                next_type=section.next_type,
                next_id=section.next_id,
            ),
            commit_after=True
        )
    await execute(
        delete(notebook_sections).where(notebook_sections.c.id == section_id),
        commit_after=True
    )

async def get_child_sections(parent_section_id: uuid.UUID | None) -> List[NotebookSectionInDB]:
    results = await fetch_all(
        select(notebook_sections).where(notebook_sections.c.parent_section_id == parent_section_id)
    )
    return [NotebookSectionInDB(**result) for result in results]

async def delete_notebook_section_recursive(section_id: uuid.UUID) -> None:
    # Find all child sections
    child_sections = await get_child_sections(section_id)
    # Recursively delete all child sections first
    for child in child_sections:
        await delete_notebook_section_recursive(child.id)
    # Delete the current section (and its analysis results)
    await delete_notebook_section(section_id)




### Helper functions
async def create_notebook() -> NotebookInDB:
    notebook = NotebookInDB(
        id=uuid.uuid4()
    )
    await execute(
        insert(notebooks).values(
            **notebook.model_dump()
        ),
        commit_after=True
    )
    return notebook

async def get_notebook_by_id(notebook_id: uuid.UUID) -> Notebook:
    result = await fetch_one(
        select(notebooks).where(notebooks.c.id == notebook_id)
    )
    if result is None:
        raise HTTPException(
            status_code=404, detail="Notebook not found"
        )
    
    # Get notebook sections
    notebook_sections = await get_notebook_sections_by_notebook_id(notebook_id)
    
    return Notebook(**result, notebook_sections=notebook_sections)


async def get_notebook_sections_by_notebook_id(notebook_id: uuid.UUID) -> List[NotebookSection]:
    """Get all notebook sections for a given notebook_id"""
    # Get root level sections (those with no parent)
    results = await fetch_all(
        select(notebook_sections).where(
            and_(
                notebook_sections.c.notebook_id == notebook_id,
                notebook_sections.c.parent_section_id == None
            )
        )
    )
    
    sections = []
    for result in results:
        # Get analysis results for this section
        analysis_results = await get_analysis_results_by_section_id(result["id"])
        # Get child sections (recursive)
        child_sections = await get_child_sections_recursive(result["id"])
        
        sections.append(NotebookSection(
            **result,
            analysis_results=analysis_results,
            notebook_sections=child_sections
        ))
    
    return sections

async def get_analysis_result_by_id(analysis_result_id: uuid.UUID) -> AnalysisResult:
    result = await fetch_one(
        select(analysis_results).where(analysis_results.c.id == analysis_result_id)
    )

    if result is None:
        return None

    dataset_ids = await get_dataset_ids_by_analysis_result_id(result["id"])
    data_source_ids = await get_data_source_ids_by_analysis_result_id(result["id"])

    return AnalysisResult(**result, dataset_ids=dataset_ids, data_source_ids=data_source_ids)

async def get_analysis_results_by_section_id(section_id: uuid.UUID) -> List[AnalysisResult]:
    """Get all analysis results for a given section_id"""
    # Get analysis result IDs from the mapping table
    results = await fetch_all(
        select(analysis_results).where(
            analysis_results.c.section_id == section_id
        )
    )
    
    
    analysis_results_list = []
    for result in results:
        dataset_ids = await get_dataset_ids_by_analysis_result_id(result["id"])
        data_source_ids = await get_data_source_ids_by_analysis_result_id(result["id"])
        analysis_results_list.append(AnalysisResult(**result, dataset_ids=dataset_ids, data_source_ids=data_source_ids))
    
    return analysis_results_list


async def get_analysis_results_by_ids(analysis_result_ids: List[uuid.UUID]) -> List[AnalysisResult]:
    results = await fetch_all(
        select(analysis_results).where(analysis_results.c.id.in_(analysis_result_ids))
    )

    analysis_results_list = []
    for result in results:
        dataset_ids = await get_dataset_ids_by_analysis_result_id(result["id"])
        analysis_results_list.append(AnalysisResult(**result, dataset_ids=dataset_ids))
    return analysis_results_list


async def get_child_sections_recursive(section_id: uuid.UUID) -> List[NotebookSection]:
    """Get all child sections recursively for a given section_id"""
    # Get direct child sections
    results = await fetch_all(
        select(notebook_sections).where(
            notebook_sections.c.parent_section_id == section_id
        )
    )
    
    sections = []
    for result in results:
        # Get analysis results for this child section
        analysis_results = await get_analysis_results_by_section_id(result["id"])
        # Get grandchild sections (recursive)
        grandchild_sections = await get_child_sections_recursive(result["id"])
        
        sections.append(NotebookSection(
            **result,
            analysis_results=analysis_results,
            notebook_sections=grandchild_sections
        ))
    
    return sections


async def update_analysis_result(analysis_result: AnalysisResult) -> AnalysisResult:
    # Extract only the database columns from the model
    update_data = AnalysisResultInDB(**analysis_result.model_dump())
    
    await execute(
        update(analysis_results).where(analysis_results.c.id == analysis_result.id).values(
            **update_data.model_dump()
        ),
        commit_after=True
    )
    
    # Handle dataset_ids separately since they're stored in a junction table
    if analysis_result.dataset_ids is not None:
        # First, remove existing dataset mappings
        await execute(
            delete(analysis_results_datasets).where(
                analysis_results_datasets.c.analysis_result_id == analysis_result.id
            ),
            commit_after=True
        )
        
        # Then add new dataset mappings
        if analysis_result.dataset_ids:
            for dataset_id in analysis_result.dataset_ids:
                await execute(
                    insert(analysis_results_datasets).values(
                        analysis_result_id=analysis_result.id,
                        dataset_id=dataset_id
                    ),
                    commit_after=True
                )
    if analysis_result.data_source_ids is not None:
        await execute(
            delete(analysis_results_data_sources).where(
                analysis_results_data_sources.c.analysis_result_id == analysis_result.id
            ),
            commit_after=True
        )
        if analysis_result.data_source_ids:
            for data_source_id in analysis_result.data_source_ids:
                await execute(
                    insert(analysis_results_data_sources).values(
                        analysis_result_id=analysis_result.id,
                        data_source_id=data_source_id
                    ),
                    commit_after=True
                )
    
    return analysis_result

async def get_section_by_id(section_id: uuid.UUID) -> NotebookSectionInDB:
    result = await fetch_one(
        select(notebook_sections).where(notebook_sections.c.id == section_id)
    )
    return NotebookSectionInDB(**result)

async def update_section(section_id: uuid.UUID, section_update: NotebookSectionUpdate) -> NotebookSectionInDB:
    await execute(
        update(notebook_sections).where(notebook_sections.c.id == section_id).values(
            **section_update.model_dump()
        ),
        commit_after=True
    )
    section = await get_section_by_id(section_id)
    return section

async def update_analysis_result_by_id(analysis_result_id: uuid.UUID, analysis_result_update: AnalysisResultUpdate) -> AnalysisResultInDB:
    await execute(
        update(analysis_results).where(analysis_results.c.id == analysis_result_id).values(
            **analysis_result_update.model_dump()
        ),
        commit_after=True
    )
    result = await get_analysis_result_by_id(analysis_result_id)
    return result
    

async def get_prev_element(this_id: uuid.UUID, this_type: Literal['analysis_result', 'notebook_section'], section_id: uuid.UUID) -> Tuple[Literal['analysis_result', 'notebook_section'], uuid.UUID] | Tuple[None, None]:
    analysis_result = await fetch_one(select(analysis_results).where(and_(analysis_results.c.next_type == this_type, analysis_results.c.next_id == this_id, analysis_results.c.section_id == section_id)))
    if analysis_result:
        return "analysis_result", analysis_result["id"]
    notebook_section = await fetch_one(select(notebook_sections).where(and_(notebook_sections.c.next_type == this_type, notebook_sections.c.next_id == this_id, notebook_sections.c.parent_section_id == section_id)))
    if notebook_section:
        return "notebook_section", notebook_section["id"]
    return None, None

async def move_element(move_request: MoveRequest) -> None:
    # Think you need to separate the case when changing section.

    # Get the moving element
    if move_request.moving_element_type == "analysis_result":
        moving_element = await get_analysis_result_by_id(move_request.moving_element_id)
        if moving_element.next_id == move_request.next_element_id and moving_element.next_type == move_request.next_element_type and moving_element.section_id == move_request.new_section_id:
            return None
    elif move_request.moving_element_type == "notebook_section":
        moving_element = await get_notebook_section_by_id(move_request.moving_element_id)
        if moving_element.next_id == move_request.next_element_id and moving_element.next_type == move_request.next_element_type and moving_element.parent_section_id == move_request.new_section_id:
            return None
    
    new_prev_element_type, new_prev_element_id = await get_prev_element(move_request.next_element_id, move_request.next_element_type, move_request.new_section_id)
    old_prev_element_type, old_prev_element_id = await get_prev_element(move_request.moving_element_id, move_request.moving_element_type, move_request.new_section_id)
    
    # Update the old previous element's next element to the moving element's current next element
    if old_prev_element_type == "analysis_result":
        await execute(
            update(analysis_results).where(analysis_results.c.id == old_prev_element_id).values(
                next_type=moving_element.next_type,
                next_id=moving_element.next_id
            ),
            commit_after=True
        )
    elif old_prev_element_type == "notebook_section":
        await execute(
            update(notebook_sections).where(notebook_sections.c.id == old_prev_element_id).values(
                next_type=moving_element.next_type,
                next_id=moving_element.next_id
            ),
            commit_after=True
        )

    # Update the moving element's next element
    if move_request.moving_element_type == "analysis_result":
        await execute(
            update(analysis_results).where(analysis_results.c.id == moving_element.id).values(
                next_type=move_request.next_element_type,
                next_id=move_request.next_element_id,
                section_id=move_request.new_section_id
            ),
            commit_after=True
        )
    elif move_request.moving_element_type == "notebook_section":
        await execute(
            update(notebook_sections).where(notebook_sections.c.id == moving_element.id).values(
                next_type=move_request.next_element_type,
                next_id=move_request.next_element_id,
                parent_section_id=move_request.new_section_id
            ),
            commit_after=True
        )

    # Update the new previous element's next element to the moving element
    if "analysis_result" == new_prev_element_type:
        await execute(
            update(analysis_results).where(analysis_results.c.id == new_prev_element_id).values(
                next_type=move_request.moving_element_type,
                next_id=move_request.moving_element_id
            ),
            commit_after=True
        )
    elif "notebook_section" == new_prev_element_type:
        await execute(
            update(notebook_sections).where(notebook_sections.c.id == new_prev_element_id).values(
                next_type=move_request.moving_element_type,
                next_id=move_request.moving_element_id
            ),
            commit_after=True
        )
        
    return None

    



# Does this belong here? Aren't service.py meant for database operations?


def build_ordered_list(sections: List[NotebookSection], results: List[AnalysisResult], first_id: uuid.UUID | None, first_type: str | None) -> List[dict]:
    """
    Build ordered list from nextType/nextId chain, similar to the client-side utils.ts function.
    Returns a list of dictionaries with 'type' and 'data' keys.
    """
    ordered_list = []
    sections_map = {s.id: s for s in sections}
    results_map = {r.id: r for r in results}
    
    current_id = first_id
    current_type = first_type
    
    while current_id and current_type:
        if current_type == "notebook_section":
            section = sections_map.get(current_id)
            if section:
                ordered_list.append({"type": "section", "data": section})
                current_id = section.next_id
                current_type = section.next_type
            else:
                break
        elif current_type == "analysis_result":
            result = results_map.get(current_id)
            if result:
                ordered_list.append({"type": "analysis_result", "data": result})
                current_id = result.next_id
                current_type = result.next_type
            else:
                break
        else:
            break
    
    return ordered_list


async def generate_notebook_report(analysis_object: AnalysisObjectInDB, include_code: bool, user_id: uuid.UUID) -> str:
    """
    Generate a markdown report from the analysis object's notebook.
    
    Args:
        analysis_object: The analysis object containing the notebook
        include_code: Whether to include Python code in the report
        
    Returns:
        A markdown string representing the complete analysis report
    """
    report = f"# {analysis_object.name}\n\n"
    
    if analysis_object.description:
        report += f"**Description:** {analysis_object.description}\n\n"
    
    report += f"**Generated:** {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}\n\n"
    
    # Process notebook sections using the existing get_notebook_by_id function
    if analysis_object.notebook:
        notebook = await get_notebook_by_id(analysis_object.notebook.id)
        
        # Get all sections and results for this notebook
        all_sections = []
        all_results = []
        
        def collect_sections_and_results(sections):
            for section in sections:
                all_sections.append(section)
                all_results.extend(section.analysis_results)
                if section.notebook_sections:
                    collect_sections_and_results(section.notebook_sections)
        
        collect_sections_and_results(notebook.notebook_sections)
        
        # Find the first element (one that's not pointed to by any other element)
        referenced_ids = set()
        for section in all_sections:
            if section.next_id:
                referenced_ids.add(section.next_id)
        for result in all_results:
            if result.next_id:
                referenced_ids.add(result.next_id)
        
        # Find first section or result that's not referenced
        first_section = next((s for s in all_sections if s.id not in referenced_ids), None)
        first_result = next((r for r in all_results if r.id not in referenced_ids), None)
        
        if first_section:
            ordered_items = build_ordered_list(all_sections, all_results, first_section.id, "notebook_section")
        elif first_result:
            ordered_items = build_ordered_list(all_sections, all_results, first_result.id, "analysis_result")
        else:
            ordered_items = []
        
        # Process the ordered items
        for item in ordered_items:
            if item["type"] == "section":
                report += await section_to_markdown(item["data"], include_code, user_id, level=2)
            elif item["type"] == "analysis_result":
                # Handle standalone analysis results (though this is unusual)
                report += await analysis_result_to_markdown(item["data"], include_code, user_id)
    
    return report


async def section_to_markdown(section: NotebookSection, include_code: bool, user_id: uuid.UUID, level: int = 1) -> str:
    """Process a notebook section and its nested sections recursively."""
    content = ""
    
    # Add section header
    header_prefix = "#" * min(level + 1, 6)  # Limit to h6
    content += f"{header_prefix} {section.section_name}\n\n"
    
    # Add section description if available
    if section.section_description:
        content += f"{section.section_description}\n\n"
    
    # Get all sections and results for this section
    child_sections = section.notebook_sections or []
    analysis_results = section.analysis_results or []
    
    # Find the first element in the chain for this section's children
    referenced_ids = set()
    for s in child_sections:
        if s.next_id:
            referenced_ids.add(s.next_id)
    for r in analysis_results:
        if r.next_id:
            referenced_ids.add(r.next_id)
    
    first_child_section = next((s for s in child_sections if s.id not in referenced_ids), None)
    first_result = next((r for r in analysis_results if r.id not in referenced_ids), None)
    
    ordered_children = []
    if first_child_section:
        ordered_children = build_ordered_list(child_sections, analysis_results, first_child_section.id, "notebook_section")
    elif first_result:
        ordered_children = build_ordered_list(child_sections, analysis_results, first_result.id, "analysis_result")
    
    # Process the ordered children
    for child in ordered_children:
        if child["type"] == "section":
            content += await section_to_markdown(child["data"], include_code, level + 1)
        elif child["type"] == "analysis_result":
            content += await analysis_result_to_markdown(child["data"], include_code, user_id)
    
    return content


async def analysis_result_to_markdown(result: AnalysisResult, include_code: bool, user_id: uuid.UUID) -> str:
    """Process an analysis result and include plots."""
    content = ""
    
    # Add analysis content
    content += f"{result.analysis}\n\n"
    
    if include_code and result.python_code:
        content += f"**Python Code:**\n```python\n{result.python_code}\n```\n\n"
    
    # Add plots for this analysis result
    from synesis_api.modules.plots.service import get_plots_by_analysis_result_id, render_plot_to_png_pyecharts
    from synesis_api.modules.data_objects.service.raw_data_service import get_aggregation_object_payload_data_by_analysis_result_id
    
    plots = await get_plots_by_analysis_result_id(result.id)
    if plots:
        # Get aggregation data for the plots
        aggregation_data = await get_aggregation_object_payload_data_by_analysis_result_id(user_id, result.id)
        for plot in plots:
            try:
                b64 = await render_plot_to_png_pyecharts(plot, aggregation_data)
                content += f"""
<div style="padding: 0 20px; box-sizing: border-box;">
<img
    src="data:image/png;base64,{b64}"
    style="width:100%; height:auto; display:block; margin: 0 auto;"
    alt="chart"
/>
</div>"""
            except Exception as e:
                print("We get an exception")
                content += f"*Error rendering plot: {str(e)}*\n\n"

    
    return content