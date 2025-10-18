import uuid
from fastapi import HTTPException
from sqlalchemy import select, insert, delete
from typing import List


from synesis_api.database.service import execute, fetch_one, fetch_all
from synesis_api.modules.analysis.models import (
    analysis_object,
    notebook_section,
    notebook,
)
# from synesis_api.modules.orchestrator.models import analysis_context
from synesis_schemas.main_server import (
    Analysis,
    AnalysisObjectCreate,
    AnalysisObjectInDB,
    AnalysisObjectSmall,
    AnalysisObjectList,
    # RemoveEntityFromProject
)
# from synesis_api.modules.project.service import remove_entity_from_project
from synesis_api.modules.analysis.service.service_utils import deep_exclude
from synesis_api.modules.analysis.service.service_notebook import (
    create_notebook,
    get_notebook_by_id,
    delete_notebook_section_recursive,
)


async def create_analysis_object(analysis_object_create: AnalysisObjectCreate, user_id: uuid.UUID) -> AnalysisObjectInDB:

    analysis_object_id = uuid.uuid4()
    notebook_in_db = await create_notebook()

    analysis_object_in_db = AnalysisObjectInDB(
        id=analysis_object_id,
        user_id=user_id,
        notebook_id=notebook_in_db.id,
        **analysis_object_create.model_dump(),
    )

    await execute(
        insert(analysis_object).values(
            **analysis_object_in_db.model_dump(exclude={"dataset_ids"})
        ),
        commit_after=True
    )

    return analysis_object_in_db


async def get_analysis_object_by_id(analysis_object_id: uuid.UUID) -> Analysis:
    result = await fetch_one(
        select(analysis_object).where(
            analysis_object.c.id == analysis_object_id)
    )
    if result is None:
        raise HTTPException(
            status_code=404, detail="Analysis object not found"
        )

    notebook = await get_notebook_by_id(result["notebook_id"])

    return Analysis(**result, notebook=notebook)


async def get_analysis_objects_small_by_project_id(project_id: uuid.UUID) -> AnalysisObjectList:
    results = await fetch_all(
        select(analysis_object).where(
            analysis_object.c.project_id == project_id)
    )

    analysis_objects_list = []
    for result in results:
        analysis_objects_list.append(AnalysisObjectSmall(**result))

    return AnalysisObjectList(analysis_objects=analysis_objects_list)


async def get_analysis_objects_by_project_id(project_id: uuid.UUID) -> List[Analysis]:
    results = await fetch_all(
        select(analysis_object).where(
            analysis_object.c.project_id == project_id)
    )

    analysis_objects_list = []
    for result in results:
        notebook = await get_notebook_by_id(result["notebook_id"])
        analysis_objects_list.append(
            Analysis(**result, notebook=notebook))

    return analysis_objects_list


async def get_user_analyses(user_id: uuid.UUID, analysis_ids: List[uuid.UUID]) -> List[Analysis]:
    results = await fetch_all(
        select(analysis_object).where(
            analysis_object.c.user_id == user_id,
            analysis_object.c.id.in_(analysis_ids)
        )
    )

    analysis_objects_list = []
    for result in results:
        notebook = await get_notebook_by_id(result["notebook_id"])
        analysis_objects_list.append(
            Analysis(**result, notebook=notebook))

    return analysis_objects_list


async def get_simplified_overview_for_context_message(user_id: uuid.UUID, analysis_ids: list[uuid.UUID]) -> str:
    analysis_objects = await get_user_analyses(user_id, analysis_ids)
    simplified_overview = [deep_exclude(analysis_object.model_dump(), set(
        ["analysis", "python_code", "input_variable"])) for analysis_object in analysis_objects]
    return simplified_overview


async def delete_analysis_object(analysis_object_id: uuid.UUID, user_id: uuid.UUID) -> uuid.UUID:
    analysis_object = await get_analysis_object_by_id(analysis_object_id)

    sections_to_delete = await fetch_all(
        select(notebook_section).where(
            notebook_section.c.notebook_id == analysis_object.notebook.id,
            notebook_section.c.parent_section_id == None
        )
    )

    section_ids = [section["id"] for section in sections_to_delete]

    for section_id in section_ids:
        await delete_notebook_section_recursive(section_id)

    # await remove_entity_from_project(analysis_object.project_id, RemoveEntityFromProject(entity_type="analysis", entity_id=analysis_object_id))

    # await execute(
    #     delete(analysis_context).where(
    #         analysis_context.c.analysis_id == analysis_object_id),
    #     commit_after=True
    # )

    await execute(
        delete(notebook).where(notebook.c.id == analysis_object.notebook.id),
        commit_after=True
    )

    await execute(
        delete(analysis_object).where(
            analysis_object.c.id == analysis_object_id),
        commit_after=True
    )

    return analysis_object_id
