import uuid
from fastapi import HTTPException
from sqlalchemy import update, select, insert, delete, and_
from typing import List
from synesis_api.database.service import execute, fetch_one, fetch_all
from synesis_api.modules.analysis.models import (
    analysis_object, 
    analysis_result, 
    notebook_section,
    notebook,
)
from synesis_schemas.main_server import (
    NotebookSectionCreate,
    NotebookSectionInDB,
    NotebookInDB,
    Notebook,
    NotebookSection,
    MoveRequest,
    NotebookSectionUpdate,
)

from .service_utils import (
    get_last_element_in_section,
    get_prev_element,
)
from .service_analysis_result import (
    get_analysis_result_by_id,
    get_analysis_results_by_section_id,
    delete_analysis_result,
)

async def create_section(notebook_section_create: NotebookSectionCreate) -> NotebookSectionInDB:
    analysis_object_from_db = await fetch_one(
        select(analysis_object).where(analysis_object.c.id == notebook_section_create.analysis_object_id)
    )
    last_type, last_id = await get_last_element_in_section(notebook_section_create.parent_section_id, analysis_object_from_db["notebook_id"])

    notebook_section_in_db = NotebookSectionInDB(
        id=uuid.uuid4(),
        **notebook_section_create.model_dump(),
        notebook_id=analysis_object_from_db["notebook_id"]
    )
    await execute(
        insert(notebook_section).values(
            **notebook_section_in_db.model_dump()
        ),
        commit_after=True
    )


    if last_type == "analysis_result":
        await execute(
            update(analysis_result).where(analysis_result.c.id == last_id).values(
                next_type="notebook_section",
                next_id=notebook_section_in_db.id
            ),
            commit_after=True
        )
    elif last_type == "notebook_section":
        await execute(
            update(notebook_section).where(notebook_section.c.id == last_id).values(
                next_type="notebook_section",
                next_id=notebook_section_in_db.id
            ),
            commit_after=True
        )
    return notebook_section


async def get_notebook_section_by_id(section_id: uuid.UUID) -> NotebookSectionInDB:
    result = await fetch_one(
        select(notebook_section).where(notebook_section.c.id == section_id)
    )
    return NotebookSectionInDB(**result)

async def delete_notebook_section(section_id: uuid.UUID) -> None:
    # Delete associated analysis results first due to foreign key constraints
    analysis_results_for_section = await get_analysis_results_by_section_id(section_id)
    for analysis_result_from_db in analysis_results_for_section:
        await delete_analysis_result(analysis_result_from_db.id)
    
    # Then delete the section itself
    section = await get_notebook_section_by_id(section_id)
    last_type, last_id = await get_prev_element(section.id, "notebook_section", section.parent_section_id)
    
    if last_type == "analysis_result":
        await execute(
            update(analysis_result).where(analysis_result.c.id == last_id).values(
                next_type=section.next_type,
                next_id=section.next_id,
            ),
            commit_after=True
        )
    elif last_type == "notebook_section":
        await execute(
            update(notebook_section).where(notebook_section.c.id == last_id).values(
                next_type=section.next_type,
                next_id=section.next_id,
            ),
            commit_after=True
        )
    await execute(
        delete(notebook_section).where(notebook_section.c.id == section_id),
        commit_after=True
    )

async def get_child_sections(parent_section_id: uuid.UUID | None) -> List[NotebookSectionInDB]:
    results = await fetch_all(
        select(notebook_section).where(notebook_section.c.parent_section_id == parent_section_id)
    )
    return [NotebookSectionInDB(**result) for result in results]

async def delete_notebook_section_recursive(section_id: uuid.UUID) -> None:
    child_sections = await get_child_sections(section_id)
    for child in child_sections:
        await delete_notebook_section_recursive(child.id)
    await delete_notebook_section(section_id)


async def create_notebook() -> NotebookInDB:
    notebook = NotebookInDB(
        id=uuid.uuid4()
    )
    await execute(
        insert(notebook).values(
            **notebook.model_dump()
        ),
        commit_after=True
    )
    return notebook

async def get_notebook_by_id(notebook_id: uuid.UUID) -> Notebook:
    result = await fetch_one(
        select(notebook).where(notebook.c.id == notebook_id)
    )
    if result is None:
        raise HTTPException(
            status_code=404, detail="Notebook not found"
        )
    
    notebook_sections = await get_notebook_sections_by_notebook_id(notebook_id)
    
    return Notebook(**result, notebook_sections=notebook_sections)


async def get_notebook_sections_by_notebook_id(notebook_id: uuid.UUID) -> List[NotebookSection]:
    results = await fetch_all(
        select(notebook_section).where(
            and_(
                notebook_section.c.notebook_id == notebook_id,
                notebook_section.c.parent_section_id == None
            )
        )
    )
    
    sections = []
    for result in results:
        analysis_results = await get_analysis_results_by_section_id(result["id"])
        child_sections = await get_child_sections_recursive(result["id"])
        
        sections.append(NotebookSection(
            **result,
            analysis_results=analysis_results,
            notebook_sections=child_sections
        ))
    
    return sections


async def get_child_sections_recursive(section_id: uuid.UUID) -> List[NotebookSection]:
    results = await fetch_all(
        select(notebook_section).where(
            notebook_section.c.parent_section_id == section_id
        )
    )
    
    sections = []
    for result in results:
        analysis_results = await get_analysis_results_by_section_id(result["id"])
        grandchild_sections = await get_child_sections_recursive(result["id"])
        
        sections.append(NotebookSection(
            **result,
            analysis_results=analysis_results,
            notebook_sections=grandchild_sections
        ))
    
    return sections



async def get_section_by_id(section_id: uuid.UUID) -> NotebookSectionInDB:
    result = await fetch_one(
        select(notebook_section).where(notebook_section.c.id == section_id)
    )
    return NotebookSectionInDB(**result)

async def update_section(section_id: uuid.UUID, section_update: NotebookSectionUpdate) -> NotebookSectionInDB:
    await execute(
        update(notebook_section).where(notebook_section.c.id == section_id).values(
            **section_update.model_dump()
        ),
        commit_after=True
    )
    section = await get_section_by_id(section_id)
    return section




async def move_element(move_request: MoveRequest) -> None:
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
            update(analysis_result).where(analysis_result.c.id == old_prev_element_id).values(
                next_type=moving_element.next_type,
                next_id=moving_element.next_id
            ),
            commit_after=True
        )
    elif old_prev_element_type == "notebook_section":
        await execute(
            update(notebook_section).where(notebook_section.c.id == old_prev_element_id).values(
                next_type=moving_element.next_type,
                next_id=moving_element.next_id
            ),
            commit_after=True
        )

    # Update the moving element's next element
    if move_request.moving_element_type == "analysis_result":
        await execute(
            update(analysis_result).where(analysis_result.c.id == moving_element.id).values(
                next_type=move_request.next_element_type,
                next_id=move_request.next_element_id,
                section_id=move_request.new_section_id
            ),
            commit_after=True
        )
    elif move_request.moving_element_type == "notebook_section":
        await execute(
            update(notebook_section).where(notebook_section.c.id == moving_element.id).values(
                next_type=move_request.next_element_type,
                next_id=move_request.next_element_id,
                parent_section_id=move_request.new_section_id
            ),
            commit_after=True
        )

    # Update the new previous element's next element to the moving element
    if "analysis_result" == new_prev_element_type:
        await execute(
            update(analysis_result).where(analysis_result.c.id == new_prev_element_id).values(
                next_type=move_request.moving_element_type,
                next_id=move_request.moving_element_id
            ),
            commit_after=True
        )
    elif "notebook_section" == new_prev_element_type:
        await execute(
            update(notebook_section).where(notebook_section.c.id == new_prev_element_id).values(
                next_type=move_request.moving_element_type,
                next_id=move_request.moving_element_id
            ),
            commit_after=True
        )
        
    return None