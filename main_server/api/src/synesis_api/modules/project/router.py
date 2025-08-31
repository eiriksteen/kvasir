from typing import List
from uuid import UUID
from fastapi import APIRouter, Depends, HTTPException
from synesis_api.auth.schema import User
from synesis_api.auth.service import get_current_user
from synesis_api.modules.project.schema import Project, ProjectCreate, ProjectDetailsUpdate, AddEntityToProject, RemoveEntityFromProject
from synesis_api.modules.project.service import (
    create_project,
    get_project,
    update_project_details,
    add_entity_to_project,
    remove_entity_from_project,
    delete_project,
    get_user_projects
)


router = APIRouter()


@router.post("/create-project", response_model=Project)
async def create_new_project(
    project_data: ProjectCreate,
    user: User = Depends(get_current_user)
) -> Project:
    return await create_project(user.id, project_data)


@router.get("/get-project/{project_id}", response_model=Project)
async def get_project_by_id(
    project_id: UUID,
    user: User = Depends(get_current_user)
) -> Project:
    project = await get_project(project_id)
    if not project:
        raise HTTPException(status_code=404, detail="Project not found")
    if project.user_id != user.id:
        raise HTTPException(
            status_code=403, detail="Not authorized to access this project")
    return project


@router.put("/update-project/{project_id}", response_model=Project)
async def update_project_details_by_id(
    project_id: UUID,
    project_data: ProjectDetailsUpdate,
    user: User = Depends(get_current_user)
) -> Project:
    """Update project name and/or description."""
    project = await get_project(project_id)
    if not project:
        raise HTTPException(status_code=404, detail="Project not found")
    if project.user_id != user.id:
        raise HTTPException(
            status_code=403, detail="Not authorized to update this project")

    updated_project = await update_project_details(project_id, project_data)
    if not updated_project:
        raise HTTPException(
            status_code=404, detail="Project not found after update")
    return updated_project


@router.post("/add-entity/{project_id}", response_model=Project)
async def add_entity_to_project_by_id(
    project_id: UUID,
    entity_data: AddEntityToProject,
    user: User = Depends(get_current_user)
) -> Project:
    """Add an entity (data source, dataset, analysis, pipeline) to a project."""
    project = await get_project(project_id)
    if not project:
        raise HTTPException(status_code=404, detail="Project not found")
    if project.user_id != user.id:
        raise HTTPException(
            status_code=403, detail="Not authorized to modify this project")

    updated_project = await add_entity_to_project(project_id, entity_data)
    if not updated_project:
        raise HTTPException(
            status_code=404, detail="Project not found after adding entity")
    return updated_project


@router.delete("/remove-entity/{project_id}", response_model=Project)
async def remove_entity_from_project_by_id(
    project_id: UUID,
    entity_data: RemoveEntityFromProject,
    user: User = Depends(get_current_user)
) -> Project:
    """Remove an entity (data source, dataset, analysis, pipeline) from a project."""
    project = await get_project(project_id)
    if not project:
        raise HTTPException(status_code=404, detail="Project not found")
    if project.user_id != user.id:
        raise HTTPException(
            status_code=403, detail="Not authorized to modify this project")

    updated_project = await remove_entity_from_project(project_id, entity_data)
    if not updated_project:
        raise HTTPException(
            status_code=404, detail="Project not found after removing entity")
    return updated_project


@router.delete("/delete-project/{project_id}")
async def delete_project_by_id(
    project_id: UUID,
    user: User = Depends(get_current_user)
) -> dict:
    project = await get_project(project_id)
    if not project:
        raise HTTPException(status_code=404, detail="Project not found")
    if project.user_id != user.id:
        raise HTTPException(
            status_code=403, detail="Not authorized to delete this project")

    await delete_project(project_id)
    return {"message": "Project deleted successfully"}


@router.get("/get-user-projects", response_model=List[Project])
async def list_all_projects(
    user: User = Depends(get_current_user)
) -> List[Project]:
    return await get_user_projects(user.id)
