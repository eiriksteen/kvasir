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
    EntityPositionCreate,
    ProjectGraph,
    DataSourceInGraph,
    ModelEntityInGraph,
    DatasetInGraph,
    PipelineInGraph,
    AnalysisInGraph,
    DataSource,
    Dataset,
    Pipeline,
    ModelEntity,
    Analysis,
    UpdateEntityPosition,
)
from synesis_api.modules.project.agent import project_agent
from synesis_api.modules.data_sources.service import get_user_data_sources
from synesis_api.modules.data_objects.service import get_user_datasets
from synesis_api.modules.pipeline.service import get_user_pipelines
from synesis_api.modules.model.service import get_user_model_entities
from synesis_api.modules.analysis.service import get_user_analyses
from synesis_api.modules.analysis.service.service_utils import get_dataset_ids_from_analysis_object, get_data_source_ids_from_analysis_object


async def create_project(user_id: UUID, project_data: ProjectCreate) -> Project:
    query = insert(project).values(
        user_id=user_id,
        name=project_data.name,
        description=project_data.description
    ).returning(project)

    project_row = await fetch_one(query, commit_after=True)
    return Project(**project_row)


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


async def get_projects(user_id: UUID, project_ids: Optional[List[UUID]] = None) -> List[Project]:
    # Get project details
    query = select(project).where(project.c.user_id == user_id)
    if project_ids is not None:
        query = query.where(project.c.id.in_(project_ids))
    project_rows = await fetch_all(query)
    project_ids = [p["id"] for p in project_rows]

    if not project_rows:
        return []

    data_source_objs = await fetch_all(select(project_data_source).where(project_data_source.c.project_id.in_(project_ids)))
    dataset_objs = await fetch_all(select(project_dataset).where(project_dataset.c.project_id.in_(project_ids)))
    analysis_objs = await fetch_all(select(project_analysis).where(project_analysis.c.project_id.in_(project_ids)))
    pipeline_objs = await fetch_all(select(project_pipeline).where(project_pipeline.c.project_id.in_(project_ids)))
    model_entity_objs = await fetch_all(select(project_model_entity).where(project_model_entity.c.project_id.in_(project_ids)))

    project_objects = []
    for project_id in project_ids:
        project_row = next((p for p in project_rows if p["id"] == project_id))
        data_sources_in_project = [
            d for d in data_source_objs if d["project_id"] == project_id]
        datasets_in_project = [
            d for d in dataset_objs if d["project_id"] == project_id]
        analyses_in_project = [
            d for d in analysis_objs if d["project_id"] == project_id]
        pipelines_in_project = [
            d for d in pipeline_objs if d["project_id"] == project_id]
        model_entities_in_project = [
            d for d in model_entity_objs if d["project_id"] == project_id]

        project_objects.append(Project(
            **project_row,
            data_sources=data_sources_in_project,
            datasets=datasets_in_project,
            analyses=analyses_in_project,
            pipelines=pipelines_in_project,
            model_entities=model_entities_in_project
        ))

    return project_objects


async def get_project_graph(user_id: UUID, project_id: UUID) -> ProjectGraph:
    project = await get_projects(user_id, [project_id])
    if not project:
        raise HTTPException(status_code=404, detail="Project not found")
    project = project[0]

    data_sources = await get_user_data_sources(user_id=user_id, data_source_ids=[ds.data_source_id for ds in project.data_sources])
    datasets = await get_user_datasets(user_id=user_id, dataset_ids=[ds.dataset_id for ds in project.datasets])
    pipelines = await get_user_pipelines(user_id=user_id, pipeline_ids=[ds.pipeline_id for ds in project.pipelines])
    model_entities = await get_user_model_entities(user_id=user_id, model_entity_ids=[ds.model_entity_id for ds in project.model_entities])
    analyses = await get_user_analyses(user_id=user_id, analysis_ids=[ds.analysis_id for ds in project.analyses])

    def _get_data_sources_in_graph(data_sources: List[DataSource], project_data_sources: List[ProjectDataSourceInDB], datasets: List[Dataset]) -> List[DataSourceInGraph]:
        objs = []
        for ds, project_ds in zip(data_sources, project_data_sources):
            output_dataset_ids = [
                dset.id for dset in datasets if ds.id in dset.sources.data_source_ids]
            output_analysis_ids = []
            objs.append(DataSourceInGraph(
                id=ds.id,
                name=ds.name,
                type=ds.type,
                brief_description=f"{ds.name} {ds.type} data source",
                x_position=project_ds.x_position,
                y_position=project_ds.y_position,
                to_datasets=output_dataset_ids,
                to_analyses=output_analysis_ids
            ))
        return objs

    def _get_datasets_in_graph(datasets: List[Dataset], project_datasets: List[ProjectDatasetInDB], pipelines: List[Pipeline]) -> List[DatasetInGraph]:
        objs = []
        for ds, project_ds in zip(datasets, project_datasets):
            output_pipeline_ids = [
                p.id for p in pipelines if ds.id in p.inputs.dataset_ids]
            output_analysis_ids = []

            objs.append(DatasetInGraph(
                id=ds.id,
                name=ds.name,
                brief_description=ds.description,
                x_position=project_ds.x_position,
                y_position=project_ds.y_position,
                to_pipelines=output_pipeline_ids,
                to_analyses=output_analysis_ids,
                from_data_sources=ds.sources.data_source_ids,
                from_datasets=ds.sources.dataset_ids,
                from_pipelines=ds.sources.pipeline_ids
            ))
        return objs

    def _get_pipelines_in_graph(pipelines: List[Pipeline], project_pipelines: List[ProjectPipelineInDB], datasets: List[Dataset], model_entities: List[ModelEntity]) -> List[PipelineInGraph]:
        objs = []
        for p, project_p in zip(pipelines, project_pipelines):
            output_dataset_ids = [
                ds.id for ds in datasets if p.id in ds.sources.pipeline_ids]
            output_model_entity_ids = [
                me.id for me in model_entities if p.id == me.implementation.pipeline_id]

            objs.append(PipelineInGraph(
                id=p.id,
                name=p.name,
                brief_description=p.description,
                x_position=project_p.x_position,
                y_position=project_p.y_position,
                from_data_sources=p.inputs.data_source_ids,
                from_datasets=p.inputs.dataset_ids,
                from_model_entities=p.inputs.model_entity_ids,
                from_analyses=p.inputs.analysis_ids,
                to_datasets=output_dataset_ids,
                to_model_entities=output_model_entity_ids
            ))
        return objs

    def _get_analyses_in_graph(analysis_object_list: List[Analysis], project_analyses: List[ProjectAnalysisInDB]) -> List[AnalysisInGraph]:
        objs = []
        for analysis_object, project_analysis in zip(analysis_object_list, project_analyses):
            analysis_object_dataset_ids = get_dataset_ids_from_analysis_object(
                analysis_object)
            analysis_object_data_source_ids = get_data_source_ids_from_analysis_object(
                analysis_object)

            objs.append(AnalysisInGraph(
                id=analysis_object.id,
                name=analysis_object.name,
                x_position=project_analysis.x_position,
                y_position=project_analysis.y_position,
                brief_description=analysis_object.description,
                from_datasets=analysis_object_dataset_ids,
                from_data_sources=analysis_object_data_source_ids,
            ))
        return objs

    def _get_model_entities_in_graph(model_entities: List[ModelEntity], project_model_entities: List[ProjectModelEntityInDB], pipelines: List[Pipeline]) -> List[ModelEntityInGraph]:
        objs = []
        for me, project_me in zip(model_entities, project_model_entities):
            output_pipeline_ids = [
                p.id for p in pipelines if me.id in p.inputs.model_entity_ids]
            objs.append(ModelEntityInGraph(
                id=me.id,
                name=me.name,
                x_position=project_me.x_position,
                y_position=project_me.y_position,
                brief_description=me.description,
                to_pipelines=output_pipeline_ids,
            ))
        return objs

    data_sources_in_graph = _get_data_sources_in_graph(
        data_sources, project.data_sources, datasets)
    datasets_in_graph = _get_datasets_in_graph(
        datasets, project.datasets, pipelines)
    pipelines_in_graph = _get_pipelines_in_graph(
        pipelines, project.pipelines, datasets, model_entities)
    analyses_in_graph = _get_analyses_in_graph(analyses, project.analyses)
    model_entities_in_graph = _get_model_entities_in_graph(
        model_entities, project.model_entities, pipelines)

    return ProjectGraph(
        data_sources=data_sources_in_graph,
        datasets=datasets_in_graph,
        pipelines=pipelines_in_graph,
        analyses=analyses_in_graph,
        model_entities=model_entities_in_graph
    )


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
    entity_position = await _generate_entity_position(user_id, entity_data)

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
    """Update the position of an entity (data source, dataset, analysis, pipeline) in a project."""
    if position_data.entity_type == "data_source":
        target_table, target_column = project_data_source, project_data_source.c.data_source_id
    elif position_data.entity_type == "dataset":
        target_table, target_column = project_dataset, project_dataset.c.dataset_id
    elif position_data.entity_type == "analysis":
        target_table, target_column = project_analysis, project_analysis.c.analysis_id
    elif position_data.entity_type == "pipeline":
        target_table, target_column = project_pipeline, project_pipeline.c.pipeline_id
    elif position_data.entity_type == "model_entity":
        target_table, target_column = project_model_entity, project_model_entity.c.model_entity_id

    await execute(update(target_table).where(and_(target_table.c.project_id == position_data.project_id, target_column == position_data.entity_id)).values(x_position=position_data.x_position, y_position=position_data.y_position), commit_after=True)

    project_obj = await get_projects(user_id, [position_data.project_id])
    return project_obj[0] if project_obj else None


#

async def _generate_entity_position(user_id: UUID, entity_data: AddEntityToProject) -> EntityPositionCreate:
    """Generate a suitable position for an entity."""
    project_graph = await get_project_graph(user_id, entity_data.project_id)

    if entity_data.entity_type == "data_source":
        entity_info = await get_user_data_sources(user_id=user_id, data_source_ids=[entity_data.entity_id])
    elif entity_data.entity_type == "model_entity":
        entity_info = await get_user_model_entities(user_id=user_id, model_entity_ids=[entity_data.entity_id])
    elif entity_data.entity_type == "dataset":
        entity_info = await get_user_datasets(user_id=user_id, dataset_ids=[entity_data.entity_id])
    elif entity_data.entity_type == "analysis":
        entity_info = await get_user_analyses(user_id=user_id, analysis_ids=[entity_data.entity_id])
    elif entity_data.entity_type == "pipeline":
        entity_info = await get_user_pipelines(user_id=user_id, pipeline_ids=[entity_data.entity_id])

    assert len(
        entity_info) == 1, f"Multiple entities found for the given ID: {entity_data.entity_id}"

    entity_info = entity_info[0]

    agent_run = await project_agent.run(
        "Now generate the position for the entity.\n" +
        f"The graph follows. Pay attention to the positions of the entities: <begin_project_graph>\n\n{project_graph.model_dump_json()}\n</begin_project_graph>\n\n" +
        f"Information about the new entity. Pay attention to the fields showing the input / output entities: <begin_entity_info>\n\n{entity_info.model_dump_json()}\n</begin_entity_info>\n\n"
    )

    return agent_run.output
