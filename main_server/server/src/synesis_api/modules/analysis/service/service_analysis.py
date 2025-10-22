import uuid
from datetime import datetime, timezone
from fastapi import HTTPException
from sqlalchemy import select, insert, delete
from typing import List, Optional, Union


from synesis_api.database.service import execute, fetch_one, fetch_all
from synesis_api.modules.analysis.models import (
    analysis,
    notebook_section,
    notebook,
    dataset_in_analysis,
    data_source_in_analysis,
    model_entity_in_analysis,
    analysis_from_past_analysis,
)
from synesis_api.modules.orchestrator.models import analysis_context
from synesis_schemas.main_server import (
    Analysis,
    AnalysisCreate,
    AnalysisInDB,
    AnalysisSmall,
    DatasetInAnalysisInDB,
    DataSourceInAnalysisInDB,
    ModelEntityInAnalysisInDB,
    AnalysisFromPastAnalysisInDB,
    AnalysisInputEntities,
)
from synesis_api.modules.analysis.service.service_utils import deep_exclude
from synesis_api.modules.analysis.service.service_notebook import (
    create_notebook,
    get_notebook_by_id,
    delete_notebook_section_recursive,
)
from synesis_api.modules.analysis.description import get_analysis_description


async def create_analysis(analysis_create: AnalysisCreate, user_id: uuid.UUID) -> AnalysisInDB:

    analysis_id = uuid.uuid4()
    notebook_in_db = await create_notebook()

    analysis_in_db = AnalysisInDB(
        id=analysis_id,
        user_id=user_id,
        notebook_id=notebook_in_db.id,
        **analysis_create.model_dump(),
    )

    dataset_in_analysis_records = [DatasetInAnalysisInDB(
        analysis_id=analysis_id,
        dataset_id=dataset_id,
        created_at=datetime.now(timezone.utc),
        updated_at=datetime.now(timezone.utc)
    ).model_dump() for dataset_id in analysis_create.input_dataset_ids]

    data_source_in_analysis_records = [DataSourceInAnalysisInDB(
        analysis_id=analysis_id,
        data_source_id=data_source_id,
        created_at=datetime.now(timezone.utc),
        updated_at=datetime.now(timezone.utc)
    ).model_dump() for data_source_id in analysis_create.input_data_source_ids]

    model_entity_in_analysis_records = [ModelEntityInAnalysisInDB(
        analysis_id=analysis_id,
        model_entity_id=model_entity_id,
        created_at=datetime.now(timezone.utc),
        updated_at=datetime.now(timezone.utc)
    ).model_dump() for model_entity_id in analysis_create.input_model_entity_ids]

    analysis_from_past_analysis_records = [AnalysisFromPastAnalysisInDB(
        analysis_id=analysis_id,
        past_analysis_id=past_analysis_id,
        created_at=datetime.now(timezone.utc),
        updated_at=datetime.now(timezone.utc)
    ).model_dump() for past_analysis_id in analysis_create.input_analysis_ids]

    await execute(
        insert(analysis).values(
            **analysis_in_db.model_dump(exclude={"dataset_ids"})
        ),
        commit_after=True
    )
    if len(dataset_in_analysis_records) > 0:
        await execute(insert(dataset_in_analysis).values(dataset_in_analysis_records), commit_after=True)
    if len(data_source_in_analysis_records) > 0:
        await execute(insert(data_source_in_analysis).values(data_source_in_analysis_records), commit_after=True)
    if len(model_entity_in_analysis_records) > 0:
        await execute(insert(model_entity_in_analysis).values(model_entity_in_analysis_records), commit_after=True)
    if len(analysis_from_past_analysis_records) > 0:
        await execute(insert(analysis_from_past_analysis).values(analysis_from_past_analysis_records), commit_after=True)

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
    analysis_ids = [record["id"] for record in analysis_object_records]

    input_dataset_ids = await fetch_all(
        select(dataset_in_analysis).where(
            dataset_in_analysis.c.analysis_id.in_(analysis_ids)
        )
    )
    input_data_source_ids = await fetch_all(
        select(data_source_in_analysis).where(
            data_source_in_analysis.c.analysis_id.in_(
                analysis_ids)
        )
    )
    input_model_entity_ids = await fetch_all(
        select(model_entity_in_analysis).where(
            model_entity_in_analysis.c.analysis_id.in_(
                analysis_ids)
        )
    )
    input_past_analysis_ids = await fetch_all(
        select(analysis_from_past_analysis).where(
            analysis_from_past_analysis.c.analysis_id.in_(
                analysis_ids)
        )
    )

    analysis_objects_list = []
    for record in analysis_object_records:
        analysis_object_id = record["id"]
        record_dataset_ids = [d["dataset_id"]
                              for d in input_dataset_ids if d["analysis_id"] == analysis_object_id]
        record_data_source_ids = [d["data_source_id"]
                                  for d in input_data_source_ids if d["analysis_id"] == analysis_object_id]
        record_model_entity_ids = [d["model_entity_id"]
                                   for d in input_model_entity_ids if d["analysis_id"] == analysis_object_id]
        record_past_analysis_ids = [d["past_analysis_id"]
                                    for d in input_past_analysis_ids if d["analysis_id"] == analysis_object_id]
        inputs = AnalysisInputEntities(
            dataset_ids=record_dataset_ids,
            data_source_ids=record_data_source_ids,
            model_entity_ids=record_model_entity_ids,
            analysis_ids=record_past_analysis_ids
        )

        if small:
            analysis_objects_list.append(
                AnalysisSmall(**record, inputs=inputs))
        else:
            record_small = AnalysisSmall(**record, inputs=inputs)
            notebook = await get_notebook_by_id(record["notebook_id"])
            description = get_analysis_description(
                record_small, notebook)
            analysis_objects_list.append(Analysis(
                **record, inputs=inputs, notebook=notebook, description_for_agent=description))

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
