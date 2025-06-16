from typing import List
from uuid import UUID
from fastapi import APIRouter, Depends, HTTPException
from synesis_api.auth.schema import User
from synesis_api.auth.service import get_current_user
from synesis_api.modules.project.schema import Project, ProjectCreate, ProjectUpdate
from synesis_api.modules.project.service import (
    create_project,
    get_project,
    update_project,
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
        raise HTTPException(status_code=403, detail="Not authorized to access this project")
    return project


@router.put("/update-project/{project_id}", response_model=Project)
async def update_project_by_id(
    project_id: UUID,
    project_data: ProjectUpdate,
    user: User = Depends(get_current_user)
) -> Project:
    project = await get_project(project_id)
    if not project:
        raise HTTPException(status_code=404, detail="Project not found")
    if project.user_id != user.id:
        raise HTTPException(status_code=403, detail="Not authorized to update this project")
    
    updated_project = await update_project(project_id, project_data)
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
        raise HTTPException(status_code=403, detail="Not authorized to delete this project")
    
    success = await delete_project(project_id)
    return {"message": "Project deleted successfully"}


@router.get("/get-user-projects", response_model=List[Project])
async def list_all_projects(
    user: User = Depends(get_current_user)
) -> List[Project]:
    return await get_user_projects(user.id)
