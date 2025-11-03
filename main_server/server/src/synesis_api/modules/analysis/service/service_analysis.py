import uuid
from sqlalchemy import select, insert, delete
from typing import List, Optional, Union


from synesis_api.database.service import execute, fetch_one, fetch_all
from synesis_api.modules.analysis.models import (
    analysis,
    notebook_section,
    notebook,
)
from synesis_api.modules.orchestrator.models import analysis_context
from synesis_schemas.main_server import (
    Analysis,
    AnalysisCreate,
    AnalysisInDB,
    AnalysisSmall,
)
from synesis_api.modules.analysis.service.service_notebook import (
    create_notebook,
    get_notebook_by_id,
    delete_notebook_section_recursive,
)


async def create_analysis(analysis_create: AnalysisCreate, user_id: uuid.UUID) -> AnalysisInDB:

    analysis_id = uuid.uuid4()
    notebook_in_db = await create_notebook()

    analysis_in_db = AnalysisInDB(
        id=analysis_id,
        user_id=user_id,
        notebook_id=notebook_in_db.id,
        **analysis_create.model_dump(),
    )

    # Input associations are now managed by project_graph module

    await execute(
        insert(analysis).values(
            **analysis_in_db.model_dump()
        ),
        commit_after=True
    )

    return analysis_in_db


async def get_user_analyses(
    user_id: uuid.UUID,
    analysis_ids: Optional[List[uuid.UUID]] = None,
    small: bool = False,
) -> List[Union[Analysis, AnalysisSmall]]:

    analysis_object_query = select(analysis).where(
        analysis.c.user_id == user_id)

    if analysis_ids is not None:
        analysis_object_query = analysis_object_query.where(
            analysis.c.id.in_(analysis_ids))

    analysis_object_records = await fetch_all(analysis_object_query)

    # Input associations are now managed by project_graph module

    analysis_objects_list = []
    for record in analysis_object_records:
        if small:
            analysis_objects_list.append(AnalysisSmall(**record))
        else:
            notebook = await get_notebook_by_id(record["notebook_id"])
            analysis_objects_list.append(Analysis(
                **record, notebook=notebook))

    return analysis_objects_list


async def delete_analysis(analysis_id: uuid.UUID, user_id: uuid.UUID) -> uuid.UUID:
    analysis_obj = (await get_user_analyses(user_id, [analysis_id]))[0]

    sections_to_delete = await fetch_all(
        select(notebook_section).where(
            notebook_section.c.notebook_id == analysis_obj.notebook.id,
            notebook_section.c.parent_section_id == None
        )
    )

    section_ids = [section["id"] for section in sections_to_delete]

    for section_id in section_ids:
        await delete_notebook_section_recursive(section_id)

    # await remove_entity_from_project(analysis_object.project_id, RemoveEntityFromProject(entity_type="analysis", entity_id=analysis_object_id))

    await execute(
        delete(analysis_context).where(
            analysis_context.c.analysis_id == analysis_id),
        commit_after=True
    )

    await execute(
        delete(notebook).where(notebook.c.id == analysis_obj.notebook.id),
        commit_after=True
    )

    await execute(
        delete(analysis).where(
            analysis.c.id == analysis_obj.id),
        commit_after=True
    )

    return analysis_id
