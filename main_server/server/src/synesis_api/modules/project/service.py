from uuid import UUID
from typing import List, Optional
from sqlalchemy import select, delete, insert, update, and_
from fastapi import HTTPException

from synesis_api.database.service import execute, fetch_one, fetch_all
from synesis_api.modules.project.models import (
    project,
    project_dataset,
    project_analysis,
    project_pipeline,
    project_data_source,
    project_model_entity
)
from synesis_schemas.main_server import (
    Project,
    ProjectCreate,
    ProjectDetailsUpdate,
    AddEntityToProject,
    RemoveEntityFromProject,
    ProjectDataSourceInDB,
    ProjectDatasetInDB,
    ProjectAnalysisInDB,
    ProjectPipelineInDB,
    ProjectModelEntityInDB,
    ProjectNodes,
    EntityPositionCreate,
    EntityGraph,
    UpdateEntityPosition,
    UpdateProjectViewport,
)
from synesis_api.modules.data_sources.service import get_user_data_sources
from synesis_api.modules.data_objects.service import get_user_datasets
from synesis_api.modules.pipeline.service import get_user_pipelines
from synesis_api.modules.model.service import get_user_model_entities
from synesis_api.modules.analysis.service import get_user_analyses
from synesis_api.modules.entity_graph.service import build_entity_graph
from synesis_api.modules.deletion.service import (
    delete_data_source as delete_data_source_entity,
    delete_dataset as delete_dataset_entity,
    delete_model_entity as delete_model_entity_entity,
    delete_pipeline as delete_pipeline_entity,
    delete_analysis as delete_analysis_entity,
)


async def create_project(user_id: UUID, project_data: ProjectCreate) -> Project:
    if project_data.python_package_name is None:
        project_data.python_package_name = project_data.name.strip().replace(
            " ", "_").lower()

    query = insert(project).values(
        user_id=user_id,
        **project_data.model_dump()
    ).returning(project)

    project_row = await fetch_one(query, commit_after=True)
    # Return project with graph field populated
    projects = await get_projects(user_id, [project_row["id"]])
    return projects[0]


async def get_project_data_sources(project_id: UUID) -> List[ProjectDataSourceInDB]:
    data_source_rows = await fetch_all(select(project_data_source).where(project_data_source.c.project_id == project_id))
    return [ProjectDataSourceInDB(**data_source_row) for data_source_row in data_source_rows]


async def get_project_datasets(project_id: UUID) -> List[ProjectDatasetInDB]:
    dataset_rows = await fetch_all(select(project_dataset).where(project_dataset.c.project_id == project_id))
    return [ProjectDatasetInDB(**dataset_row) for dataset_row in dataset_rows]


async def get_project_analyses(project_id: UUID) -> List[ProjectAnalysisInDB]:
    analysis_rows = await fetch_all(select(project_analysis).where(project_analysis.c.project_id == project_id))
    return [ProjectAnalysisInDB(**analysis_row) for analysis_row in analysis_rows]


async def get_project_pipelines(project_id: UUID) -> List[ProjectPipelineInDB]:
    pipeline_rows = await fetch_all(select(project_pipeline).where(project_pipeline.c.project_id == project_id))
    return [ProjectPipelineInDB(**pipeline_row) for pipeline_row in pipeline_rows]


async def get_project_model_entities(project_id: UUID) -> List[ProjectModelEntityInDB]:
    model_entity_rows = await fetch_all(select(project_model_entity).where(project_model_entity.c.project_id == project_id))
    return [ProjectModelEntityInDB(**model_entity_row) for model_entity_row in model_entity_rows]


async def _build_project_graph(
    user_id: UUID,
    project_data_sources: List[ProjectDataSourceInDB],
    project_datasets: List[ProjectDatasetInDB],
    project_pipelines: List[ProjectPipelineInDB],
    project_model_entities: List[ProjectModelEntityInDB],
    project_analyses: List[ProjectAnalysisInDB]
) -> EntityGraph:
    """Build a project graph from project entity lists."""
    data_sources = await get_user_data_sources(user_id=user_id, data_source_ids=[ds.data_source_id for ds in project_data_sources])
    datasets = await get_user_datasets(user_id=user_id, dataset_ids=[ds.dataset_id for ds in project_datasets])
    pipelines = await get_user_pipelines(user_id=user_id, pipeline_ids=[ds.pipeline_id for ds in project_pipelines])
    model_entities = await get_user_model_entities(user_id=user_id, model_entity_ids=[ds.model_entity_id for ds in project_model_entities])
    analyses = await get_user_analyses(user_id=user_id, analysis_ids=[ds.analysis_id for ds in project_analyses])

    return await build_entity_graph(
        data_sources=data_sources,
        datasets=datasets,
        pipelines=pipelines,
        model_entities=model_entities,
        analyses=analyses
    )


async def get_projects(user_id: UUID, project_ids: Optional[List[UUID]] = None) -> List[Project]:
    # Get project details
    query = select(project).where(project.c.user_id == user_id)
    if project_ids is not None:
        query = query.where(project.c.id.in_(project_ids))
    project_rows = await fetch_all(query)
    project_ids_list = [p["id"] for p in project_rows]

    if not project_rows:
        return []

    data_source_objs = await fetch_all(select(project_data_source).where(project_data_source.c.project_id.in_(project_ids_list)))
    dataset_objs = await fetch_all(select(project_dataset).where(project_dataset.c.project_id.in_(project_ids_list)))
    analysis_objs = await fetch_all(select(project_analysis).where(project_analysis.c.project_id.in_(project_ids_list)))
    pipeline_objs = await fetch_all(select(project_pipeline).where(project_pipeline.c.project_id.in_(project_ids_list)))
    model_entity_objs = await fetch_all(select(project_model_entity).where(project_model_entity.c.project_id.in_(project_ids_list)))

    project_objects = []
    for project_id in project_ids_list:
        project_row = next((p for p in project_rows if p["id"] == project_id))
        data_sources_in_project = [
            ProjectDataSourceInDB(**d) for d in data_source_objs if d["project_id"] == project_id]
        datasets_in_project = [
            ProjectDatasetInDB(**d) for d in dataset_objs if d["project_id"] == project_id]
        analyses_in_project = [
            ProjectAnalysisInDB(**d) for d in analysis_objs if d["project_id"] == project_id]
        pipelines_in_project = [
            ProjectPipelineInDB(**d) for d in pipeline_objs if d["project_id"] == project_id]
        model_entities_in_project = [
            ProjectModelEntityInDB(**d) for d in model_entity_objs if d["project_id"] == project_id]

        project_graph = await _build_project_graph(
            user_id,
            data_sources_in_project,
            datasets_in_project,
            pipelines_in_project,
            model_entities_in_project,
            analyses_in_project
        )

        project_nodes = ProjectNodes(
            project_data_sources=data_sources_in_project,
            project_datasets=datasets_in_project,
            project_pipelines=pipelines_in_project,
            project_analyses=analyses_in_project,
            project_model_entities=model_entities_in_project
        )

        project_objects.append(Project(
            **project_row,
            graph=project_graph,
            project_nodes=project_nodes
        ))

    return project_objects


async def update_project_details(user_id: UUID, project_data: ProjectDetailsUpdate) -> Project | None:
    """Update project name and/or description."""
    update_values = {}
    if project_data.name is not None:
        update_values["name"] = project_data.name
    if project_data.description is not None:
        update_values["description"] = project_data.description

    if update_values:
        query = update(project).where(
            and_(project.c.id == project_data.project_id, project.c.user_id == user_id)).values(**update_values)
        await execute(query, commit_after=True)

    project_obj = await get_projects(user_id, [project_data.project_id])
    return project_obj[0] if project_obj else None


async def add_entity_to_project(user_id: UUID, entity_data: AddEntityToProject) -> Project | None:
    """Add an entity (data source, dataset, analysis, pipeline) to a project."""
    entity_type = entity_data.entity_type
    entity_id = entity_data.entity_id

    # Check if the entity already exists in the project
    existing_entity = None
    if entity_type == "data_source":
        existing_entity = await fetch_one(
            select(project_data_source).where(
                and_(project_data_source.c.project_id == entity_data.project_id,
                     project_data_source.c.data_source_id == entity_id)
            )
        )
    elif entity_type == "model_entity":
        existing_entity = await fetch_one(
            select(project_model_entity).where(
                and_(project_model_entity.c.project_id == entity_data.project_id,
                     project_model_entity.c.model_entity_id == entity_id)
            )
        )
    elif entity_type == "dataset":
        existing_entity = await fetch_one(
            select(project_dataset).where(
                and_(project_dataset.c.project_id == entity_data.project_id,
                     project_dataset.c.dataset_id == entity_id)
            )
        )
    elif entity_type == "analysis":
        existing_entity = await fetch_one(
            select(project_analysis).where(
                and_(project_analysis.c.project_id == entity_data.project_id,
                     project_analysis.c.analysis_id == entity_id)
            )
        )
    elif entity_type == "pipeline":
        existing_entity = await fetch_one(
            select(project_pipeline).where(
                and_(project_pipeline.c.project_id == entity_data.project_id,
                     project_pipeline.c.pipeline_id == entity_id)
            )
        )

    # If entity already exists, just return the project
    if existing_entity is not None:
        project_obj = await get_projects(user_id, [entity_data.project_id])
        return project_obj[0] if project_obj else None

    # entity_position = await _generate_entity_position(user_id, entity_data)

    # TODO: Add more sophisticated position generation
    # Using the agent is too slow
    entity_position = EntityPositionCreate(x=200, y=200)

    if entity_type == "data_source":
        obj = ProjectDataSourceInDB(
            data_source_id=entity_id, **entity_data.model_dump(),
            x_position=entity_position.x,
            y_position=entity_position.y)
        await execute(insert(project_data_source).values(obj.model_dump()), commit_after=True)
    elif entity_type == "model_entity":
        obj = ProjectModelEntityInDB(
            model_entity_id=entity_id, **entity_data.model_dump(),
            x_position=entity_position.x,
            y_position=entity_position.y)
        await execute(insert(project_model_entity).values(obj.model_dump()), commit_after=True)
    elif entity_type == "dataset":
        obj = ProjectDatasetInDB(
            dataset_id=entity_id,
            **entity_data.model_dump(),
            x_position=entity_position.x,
            y_position=entity_position.y)
        await execute(insert(project_dataset).values(obj.model_dump()), commit_after=True)
    elif entity_type == "analysis":
        obj = ProjectAnalysisInDB(
            analysis_id=entity_id, **entity_data.model_dump(),
            x_position=entity_position.x,
            y_position=entity_position.y)
        await execute(insert(project_analysis).values(obj.model_dump()), commit_after=True)
    elif entity_type == "pipeline":
        obj = ProjectPipelineInDB(
            pipeline_id=entity_id, **entity_data.model_dump(),
            x_position=entity_position.x,
            y_position=entity_position.y)
        await execute(insert(project_pipeline).values(obj.model_dump()), commit_after=True)

    project_obj = await get_projects(user_id, [entity_data.project_id])
    return project_obj[0] if project_obj else None


async def remove_entity_from_project(user_id: UUID, entity_data: RemoveEntityFromProject) -> Project | None:
    """Remove an entity (data source, dataset, analysis, pipeline) from a project."""
    entity_type = entity_data.entity_type
    entity_id = entity_data.entity_id

    if entity_type == "data_source":
        await execute(
            delete(project_data_source).where(
                and_(project_data_source.c.project_id == entity_data.project_id,
                     project_data_source.c.data_source_id == entity_id),
            ),
            commit_after=True
        )
    elif entity_type == "dataset":
        await execute(
            delete(project_dataset).where(
                and_(project_dataset.c.project_id == entity_data.project_id,
                     project_dataset.c.dataset_id == entity_id),
            ),
            commit_after=True
        )
    elif entity_type == "analysis":
        await execute(
            delete(project_analysis).where(
                and_(project_analysis.c.project_id == entity_data.project_id,
                     project_analysis.c.analysis_id == entity_id),
            ),
            commit_after=True
        )
    elif entity_type == "pipeline":
        await execute(
            delete(project_pipeline).where(
                and_(project_pipeline.c.project_id == entity_data.project_id,
                     project_pipeline.c.pipeline_id == entity_id),
            ),
            commit_after=True
        )
    elif entity_type == "model_entity":
        await execute(
            delete(project_model_entity).where(
                and_(project_model_entity.c.project_id == entity_data.project_id,
                     project_model_entity.c.model_entity_id == entity_id),
            ),
            commit_after=True
        )

    project_obj = await get_projects(user_id, [entity_data.project_id])
    return project_obj[0] if project_obj else None


async def delete_project(user_id: UUID, project_id: UUID) -> bool:
    # Delete related records first
    await execute(delete(project_dataset).where(project_dataset.c.project_id == project_id), commit_after=True)
    await execute(delete(project_analysis).where(project_analysis.c.project_id == project_id), commit_after=True)
    await execute(delete(project_pipeline).where(project_pipeline.c.project_id == project_id), commit_after=True)
    await execute(delete(project_model_entity).where(project_model_entity.c.project_id == project_id), commit_after=True)
    await execute(delete(project_data_source).where(project_data_source.c.project_id == project_id), commit_after=True)
    # Delete project
    query = delete(project).where(
        and_(project.c.id == project_id, project.c.user_id == user_id))
    result = await execute(query, commit_after=True)

    return result.rowcount > 0


async def update_entity_position(user_id: UUID, position_data: UpdateEntityPosition) -> Project | None:
    """Update the position of a node (data source, dataset, analysis, pipeline, or model_entity) in a project."""
    if position_data.entity_type == "data_source":
        target_table, target_column = project_data_source, project_data_source.c.data_source_id
        update_values = {
            "x_position": position_data.x_position,
            "y_position": position_data.y_position
        }
    elif position_data.entity_type == "dataset":
        target_table, target_column = project_dataset, project_dataset.c.dataset_id
        update_values = {
            "x_position": position_data.x_position,
            "y_position": position_data.y_position
        }
    elif position_data.entity_type == "analysis":
        target_table, target_column = project_analysis, project_analysis.c.analysis_id
        update_values = {
            "x_position": position_data.x_position,
            "y_position": position_data.y_position
        }
    elif position_data.entity_type == "pipeline":
        target_table, target_column = project_pipeline, project_pipeline.c.pipeline_id
        update_values = {
            "x_position": position_data.x_position,
            "y_position": position_data.y_position
        }
    elif position_data.entity_type == "model_entity":
        target_table, target_column = project_model_entity, project_model_entity.c.model_entity_id
        update_values = {
            "x_position": position_data.x_position,
            "y_position": position_data.y_position
        }
    else:
        raise HTTPException(status_code=400, detail="Invalid entity type")

    await execute(
        update(target_table).where(
            and_(target_table.c.project_id == position_data.project_id,
                 target_column == position_data.entity_id)
        ).values(**update_values),
        commit_after=True)

    project_obj = await get_projects(user_id, [position_data.project_id])
    return project_obj[0] if project_obj else None


async def update_project_viewport(user_id: UUID, viewport_data: UpdateProjectViewport) -> Project | None:
    """Update the viewport position and zoom of a project."""
    query = update(project).where(
        and_(project.c.id == viewport_data.project_id,
             project.c.user_id == user_id)
    ).values(
        view_port_x=viewport_data.x,
        view_port_y=viewport_data.y,
        view_port_zoom=viewport_data.zoom
    )
    await execute(query, commit_after=True)

    project_obj = await get_projects(user_id, [viewport_data.project_id])
    return project_obj[0] if project_obj else None


async def delete_data_source_from_project(user_id: UUID, data_source_id: UUID) -> UUID:
    """
    Delete a data source entity and remove it from all projects.
    """
    # Find all projects containing this data source
    project_data_source_records = await fetch_all(
        select(project_data_source).where(
            project_data_source.c.data_source_id == data_source_id
        )
    )
    project_ids = list(set([r["project_id"]
                       for r in project_data_source_records]))

    # Remove from all projects
    for project_id in project_ids:
        await execute(
            delete(project_data_source).where(
                and_(
                    project_data_source.c.project_id == project_id,
                    project_data_source.c.data_source_id == data_source_id
                )
            ),
            commit_after=True
        )

    # Delete the entity itself
    return await delete_data_source_entity(user_id, data_source_id)


async def delete_dataset_from_project(user_id: UUID, dataset_id: UUID) -> UUID:
    """
    Delete a dataset entity and remove it from all projects.
    """
    # Find all projects containing this dataset
    project_dataset_records = await fetch_all(
        select(project_dataset).where(
            project_dataset.c.dataset_id == dataset_id
        )
    )
    project_ids = list(set([r["project_id"] for r in project_dataset_records]))

    # Remove from all projects
    for project_id in project_ids:
        await execute(
            delete(project_dataset).where(
                and_(
                    project_dataset.c.project_id == project_id,
                    project_dataset.c.dataset_id == dataset_id
                )
            ),
            commit_after=True
        )

    # Delete the entity itself
    return await delete_dataset_entity(user_id, dataset_id)


async def delete_model_entity_from_project(user_id: UUID, model_entity_id: UUID) -> UUID:
    """
    Delete a model entity and remove it from all projects.
    """
    # Find all projects containing this model entity
    project_model_entity_records = await fetch_all(
        select(project_model_entity).where(
            project_model_entity.c.model_entity_id == model_entity_id
        )
    )
    project_ids = list(set([r["project_id"]
                       for r in project_model_entity_records]))

    # Remove from all projects
    for project_id in project_ids:
        await execute(
            delete(project_model_entity).where(
                and_(
                    project_model_entity.c.project_id == project_id,
                    project_model_entity.c.model_entity_id == model_entity_id
                )
            ),
            commit_after=True
        )

    # Delete the entity itself
    return await delete_model_entity_entity(user_id, model_entity_id)


async def delete_pipeline_from_project(user_id: UUID, pipeline_id: UUID) -> UUID:
    """
    Delete a pipeline entity and remove it from all projects.
    """
    # Find all projects containing this pipeline
    project_pipeline_records = await fetch_all(
        select(project_pipeline).where(
            project_pipeline.c.pipeline_id == pipeline_id
        )
    )
    project_ids = list(set([r["project_id"]
                       for r in project_pipeline_records]))

    # Remove from all projects
    for project_id in project_ids:
        await execute(
            delete(project_pipeline).where(
                and_(
                    project_pipeline.c.project_id == project_id,
                    project_pipeline.c.pipeline_id == pipeline_id
                )
            ),
            commit_after=True
        )

    # Delete the entity itself
    return await delete_pipeline_entity(user_id, pipeline_id)


async def delete_analysis_from_project(user_id: UUID, analysis_id: UUID) -> UUID:
    """
    Delete an analysis entity and remove it from all projects.
    """
    # Find all projects containing this analysis
    project_analysis_records = await fetch_all(
        select(project_analysis).where(
            project_analysis.c.analysis_id == analysis_id
        )
    )
    project_ids = list(set([r["project_id"]
                       for r in project_analysis_records]))

    # Remove from all projects
    for project_id in project_ids:
        await execute(
            delete(project_analysis).where(
                and_(
                    project_analysis.c.project_id == project_id,
                    project_analysis.c.analysis_id == analysis_id
                )
            ),
            commit_after=True
        )

    # Delete the entity itself
    return await delete_analysis_entity(user_id, analysis_id)
