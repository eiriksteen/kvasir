from typing import List
from uuid import UUID
from sqlalchemy import select, delete, insert, update
from synesis_api.database.service import execute, fetch_one, fetch_all
from synesis_api.modules.project.models import project, project_dataset, project_analysis, project_pipeline, project_data_source, project_model, project_model_source
from synesis_schemas.main_server import Project, ProjectCreate, ProjectDetailsUpdate, AddEntityToProject, RemoveEntityFromProject


async def create_project(user_id: UUID, project_data: ProjectCreate) -> Project:
    query = insert(project).values(
        user_id=user_id,
        name=project_data.name,
        description=project_data.description
    ).returning(project)

    project_row = await fetch_one(query, commit_after=True)

    return Project(
        id=project_row["id"],
        user_id=project_row["user_id"],
        name=project_row["name"],
        description=project_row["description"],
        created_at=project_row["created_at"],
        updated_at=project_row["updated_at"]
    )


async def get_data_source_ids_in_project(project_id: UUID) -> List[UUID]:
    query = select(project_data_source.c.data_source_id).where(
        project_data_source.c.project_id == project_id)
    result = await fetch_all(query)
    return [data_source_id["data_source_id"] for data_source_id in result]


async def get_model_source_ids_in_project(project_id: UUID) -> List[UUID]:
    query = select(project_model_source.c.model_source_id).where(
        project_model_source.c.project_id == project_id)
    result = await fetch_all(query)
    return [model_source_id["model_source_id"] for model_source_id in result]


async def get_dataset_ids_in_project(project_id: UUID) -> List[UUID]:
    query = select(project_dataset.c.dataset_id).where(
        project_dataset.c.project_id == project_id)
    result = await fetch_all(query)
    return [dataset_id["dataset_id"] for dataset_id in result]


async def get_analysis_ids_in_project(project_id: UUID) -> List[UUID]:
    query = select(project_analysis.c.analysis_id).where(
        project_analysis.c.project_id == project_id)
    result = await fetch_all(query)
    return [analysis_id["analysis_id"] for analysis_id in result]


async def get_pipeline_ids_in_project(project_id: UUID) -> List[UUID]:
    query = select(project_pipeline.c.pipeline_id).where(
        project_pipeline.c.project_id == project_id)
    result = await fetch_all(query)
    return [pipeline_id["pipeline_id"] for pipeline_id in result]


async def get_model_ids_in_project(project_id: UUID) -> List[UUID]:
    query = select(project_model.c.model_id).where(
        project_model.c.project_id == project_id)
    result = await fetch_all(query)
    return [model_id["model_id"] for model_id in result]


async def get_project(project_id: UUID) -> Project | None:
    # Get project details
    query = select(project).where(project.c.id == project_id)
    project_row = await fetch_one(query)

    if not project_row:
        return None

    # Get related IDs
    data_source_ids = await get_data_source_ids_in_project(project_id)
    model_source_ids = await get_model_source_ids_in_project(project_id)
    dataset_ids = await get_dataset_ids_in_project(project_id)
    analysis_ids = await get_analysis_ids_in_project(project_id)
    pipeline_ids = await get_pipeline_ids_in_project(project_id)
    model_ids = await get_model_ids_in_project(project_id)

    return Project(
        **project_row,
        data_source_ids=data_source_ids,
        model_source_ids=model_source_ids,
        dataset_ids=dataset_ids,
        analysis_ids=analysis_ids,
        pipeline_ids=pipeline_ids,
        model_ids=model_ids
    )


async def update_project_details(project_id: UUID, project_data: ProjectDetailsUpdate) -> Project | None:
    """Update project name and/or description."""
    update_values = {}
    if project_data.name is not None:
        update_values["name"] = project_data.name
    if project_data.description is not None:
        update_values["description"] = project_data.description

    if update_values:
        query = update(project).where(
            project.c.id == project_id).values(**update_values)
        await execute(query, commit_after=True)

    return await get_project(project_id)


async def add_entity_to_project(entity_data: AddEntityToProject) -> Project | None:
    """Add an entity (data source, dataset, analysis, pipeline) to a project."""
    entity_type = entity_data.entity_type
    entity_id = entity_data.entity_id

    if entity_type == "data_source":
        await execute(
            insert(project_data_source).values(
                project_id=entity_data.project_id,
                data_source_id=entity_id
            ),
            commit_after=True
        )
    elif entity_type == "model_source":
        await execute(
            insert(project_model_source).values(
                project_id=entity_data.project_id,
                model_source_id=entity_id
            ),
            commit_after=True
        )
    elif entity_type == "dataset":
        await execute(
            insert(project_dataset).values(
                project_id=entity_data.project_id,
                dataset_id=entity_id
            ),
            commit_after=True
        )
    elif entity_type == "analysis":
        await execute(
            insert(project_analysis).values(
                project_id=entity_data.project_id,
                analysis_id=entity_id
            ),
            commit_after=True
        )
    elif entity_type == "pipeline":
        await execute(
            insert(project_pipeline).values(
                project_id=entity_data.project_id,
                pipeline_id=entity_id
            ),
            commit_after=True
        )
    elif entity_type == "model":
        await execute(
            insert(project_model).values(
                project_id=entity_data.project_id,
                model_id=entity_id
            ),
            commit_after=True
        )

    return await get_project(entity_data.project_id)


async def remove_entity_from_project(entity_data: RemoveEntityFromProject) -> Project | None:
    """Remove an entity (data source, dataset, analysis, pipeline) from a project."""
    entity_type = entity_data.entity_type
    entity_id = entity_data.entity_id

    if entity_type == "data_source":
        await execute(
            delete(project_data_source).where(
                project_data_source.c.project_id == entity_data.project_id,
                project_data_source.c.data_source_id == entity_id
            ),
            commit_after=True
        )
    elif entity_type == "model_source":
        await execute(
            delete(project_model_source).where(
                project_model_source.c.project_id == entity_data.project_id,
                project_model_source.c.model_source_id == entity_id
            ),
            commit_after=True
        )
    elif entity_type == "dataset":
        await execute(
            delete(project_dataset).where(
                project_dataset.c.project_id == entity_data.project_id,
                project_dataset.c.dataset_id == entity_id
            ),
            commit_after=True
        )
    elif entity_type == "analysis":
        await execute(
            delete(project_analysis).where(
                project_analysis.c.project_id == entity_data.project_id,
                project_analysis.c.analysis_id == entity_id
            ),
            commit_after=True
        )
    elif entity_type == "pipeline":
        await execute(
            delete(project_pipeline).where(
                project_pipeline.c.project_id == entity_data.project_id,
                project_pipeline.c.pipeline_id == entity_id
            ),
            commit_after=True
        )
    elif entity_type == "model":
        await execute(
            delete(project_model).where(
                project_model.c.project_id == entity_data.project_id,
                project_model.c.model_id == entity_id
            ),
            commit_after=True
        )
    return await get_project(entity_data.project_id)


async def delete_project(project_id: UUID) -> bool:
    # Delete related records first
    await execute(delete(project_dataset).where(project_dataset.c.project_id == project_id), commit_after=True)
    await execute(delete(project_analysis).where(project_analysis.c.project_id == project_id), commit_after=True)
    await execute(delete(project_pipeline).where(project_pipeline.c.project_id == project_id), commit_after=True)
    await execute(delete(project_model).where(project_model.c.project_id == project_id), commit_after=True)
    await execute(delete(project_model_source).where(project_model_source.c.project_id == project_id), commit_after=True)
    # Delete project
    query = delete(project).where(project.c.id == project_id)
    result = await execute(query, commit_after=True)

    return result.rowcount > 0


async def list_projects() -> List[Project]:
    query = select(project)
    projects = await fetch_all(query)

    return [
        await get_project(project_row["id"])
        for project_row in projects
    ]


async def get_user_projects(user_id: UUID) -> List[Project]:
    query = select(project).where(project.c.user_id == user_id)
    projects = await fetch_all(query)

    # Should write query instead of iterating
    return [
        await get_project(project_row["id"])
        for project_row in projects
    ]
