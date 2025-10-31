from typing import List, Annotated
from uuid import UUID
from fastapi import APIRouter, Depends, HTTPException

from synesis_schemas.main_server import User
from synesis_api.auth.service import get_current_user
from synesis_schemas.main_server import (
    Project,
    ProjectCreate,
    ProjectDetailsUpdate,
    AddEntityToProject,
    RemoveEntityFromProject,
    UpdateEntityPosition,
    UpdateProjectViewport,
    Dataset,
    DataSource,
    Analysis,
    Pipeline,
    ModelEntity,
)
from synesis_api.modules.project.service import (
    create_project,
    get_projects,
    update_project_details,
    add_entity_to_project,
    remove_entity_from_project,
    delete_project,
    update_entity_position,
    update_project_viewport,
    get_project_datasets,
    get_project_data_sources,
    get_project_analyses,
    get_project_pipelines,
    get_project_model_entities
)
from synesis_api.modules.data_objects.service import get_user_datasets
from synesis_api.modules.data_sources.service import get_user_data_sources
from synesis_api.modules.analysis.service import get_user_analyses
from synesis_api.modules.pipeline.service import get_user_pipelines
from synesis_api.modules.model.service import get_user_model_entities


router = APIRouter()


@router.post("/create-project", response_model=Project)
async def create_new_project(
    project_data: ProjectCreate,
    user: Annotated[User, Depends(get_current_user)] = None
) -> Project:
    return await create_project(user.id, project_data)


@router.get("/get-project/{project_id}", response_model=Project)
async def get_project_by_id(
    project_id: UUID,
    user: Annotated[User, Depends(get_current_user)] = None
) -> Project:
    project = await get_projects(user.id, [project_id])
    if not project:
        raise HTTPException(status_code=404, detail="Project not found")
    project = project[0]
    if project.user_id != user.id:
        raise HTTPException(
            status_code=403, detail="Not authorized to access this project")

    return project


@router.put("/update-project/{project_id}", response_model=Project)
async def update_project_details_by_id(
    project_id: UUID,
    project_data: ProjectDetailsUpdate,
    user: Annotated[User, Depends(get_current_user)] = None
) -> Project:
    """Update project name and/or description."""
    project = await get_projects(user.id, [project_id])
    if not project:
        raise HTTPException(status_code=404, detail="Project not found")
    project = project[0]
    if project.user_id != user.id:
        raise HTTPException(
            status_code=403, detail="Not authorized to update this project")

    updated_project = await update_project_details(user.id, project_data)
    if not updated_project:
        raise HTTPException(
            status_code=404, detail="Project not found after update")
    return updated_project


@router.post("/add-entity", response_model=Project)
async def post_entity_to_project(
    entity_data: AddEntityToProject,
    user: Annotated[User, Depends(get_current_user)] = None
) -> Project:
    """Add an entity (data source, dataset, analysis, pipeline) to a project."""
    project = await get_projects(user.id, [entity_data.project_id])
    if not project:
        raise HTTPException(status_code=404, detail="Project not found")
    project = project[0]
    if project.user_id != user.id:
        raise HTTPException(
            status_code=403, detail="Not authorized to modify this project")

    updated_project = await add_entity_to_project(user.id, entity_data)
    if not updated_project:
        raise HTTPException(
            status_code=404, detail="Project not found after adding entity")
    return updated_project


@router.delete("/remove-entity", response_model=Project)
async def delete_entity_from_project(
    entity_data: RemoveEntityFromProject,
    user: Annotated[User, Depends(get_current_user)] = None
) -> Project:
    """Remove an entity (data source, dataset, analysis, pipeline) from a project."""
    project = await get_projects(user.id, [entity_data.project_id])
    if not project:
        raise HTTPException(status_code=404, detail="Project not found")
    project = project[0]
    if project.user_id != user.id:
        raise HTTPException(
            status_code=403, detail="Not authorized to modify this project")

    updated_project = await remove_entity_from_project(user.id, entity_data)
    if not updated_project:
        raise HTTPException(
            status_code=404, detail="Project not found after removing entity")
    return updated_project


@router.delete("/delete-project/{project_id}")
async def delete_project_by_id(
    project_id: UUID,
    user: Annotated[User, Depends(get_current_user)] = None
) -> dict:
    project = await get_projects(user.id, [project_id])
    if not project:
        raise HTTPException(status_code=404, detail="Project not found")
    project = project[0]
    if project.user_id != user.id:
        raise HTTPException(
            status_code=403, detail="Not authorized to delete this project")

    await delete_project(user.id, project_id)
    return {"message": "Project deleted successfully"}


@router.get("/get-user-projects", response_model=List[Project])
async def list_all_projects(user: Annotated[User, Depends(get_current_user)] = None) -> List[Project]:
    return await get_projects(user.id)


@router.patch("/update-entity-position", response_model=Project)
async def patch_entity_position(
    position_data: UpdateEntityPosition,
    user: Annotated[User, Depends(get_current_user)] = None
) -> Project:
    """Update the position of an entity (data source, dataset, analysis, pipeline) in a project."""
    project = await get_projects(user.id, [position_data.project_id])
    if not project:
        raise HTTPException(status_code=404, detail="Project not found")
    project = project[0]
    if project.user_id != user.id:
        raise HTTPException(
            status_code=403, detail="Not authorized to modify this project")
    return await update_entity_position(user.id, position_data)


@router.patch("/update-project-viewport", response_model=Project)
async def patch_project_viewport(
    viewport_data: UpdateProjectViewport,
    user: Annotated[User, Depends(get_current_user)] = None
) -> Project:
    """Update the viewport position and zoom of a project."""
    project = await get_projects(user.id, [viewport_data.project_id])
    if not project:
        raise HTTPException(status_code=404, detail="Project not found")
    project = project[0]
    if project.user_id != user.id:
        raise HTTPException(
            status_code=403, detail="Not authorized to modify this project")
    return await update_project_viewport(user.id, viewport_data)


@router.get("/project-data-sources/{project_id}", response_model=List[DataSource])
async def fetch_data_sources(
    project_id: UUID,
    user: Annotated[User, Depends(get_current_user)] = None
) -> List[DataSource]:
    project_data_sources = await get_project_data_sources(project_id)
    data_sources = await get_user_data_sources(user.id, [ds.data_source_id for ds in project_data_sources])
    return data_sources


@router.get("/project-datasets/{project_id}", response_model=List[Dataset])
async def fetch_datasets(
    project_id: UUID,
    user: Annotated[User, Depends(get_current_user)] = None
) -> List[Dataset]:
    """Get all datasets for the current user"""
    project_datasets = await get_project_datasets(project_id)
    datasets = await get_user_datasets(user.id, [ds.dataset_id for ds in project_datasets])
    return datasets


@router.get("/project-analyses/{project_id}", response_model=List[Analysis])
async def fetch_analyses(
    project_id: UUID,
    user: Annotated[User, Depends(get_current_user)] = None
) -> List[Analysis]:
    project_analyses = await get_project_analyses(project_id)
    analyses = await get_user_analyses(user.id, [ds.analysis_id for ds in project_analyses])
    return analyses


@router.get("/project-pipelines/{project_id}", response_model=List[Pipeline])
async def fetch_pipelines(
    project_id: UUID,
    user: Annotated[User, Depends(get_current_user)] = None
) -> List[Pipeline]:
    project_pipelines = await get_project_pipelines(project_id)
    pipelines = await get_user_pipelines(user.id, [ds.pipeline_id for ds in project_pipelines])
    return pipelines


@router.get("/project-model-entities/{project_id}", response_model=List[ModelEntity])
async def fetch_model_entities(
    project_id: UUID,
    user: Annotated[User, Depends(get_current_user)] = None
) -> List[ModelEntity]:
    project_model_entities = await get_project_model_entities(project_id)
    model_entities = await get_user_model_entities(user.id, [ds.model_entity_id for ds in project_model_entities])
    return model_entities
