from uuid import UUID
from typing import List, Annotated
from fastapi import APIRouter, Depends

from kvasir_api.modules.project.service import get_projects_service, Projects
from kvasir_api.modules.project.schema import Project, ProjectCreate, ProjectViewPortUpdate

router = APIRouter()


@router.post("/project", response_model=Project)
async def create_project_endpoint(
    request: ProjectCreate,
    project_service: Annotated[Projects, Depends(get_projects_service)]
) -> Project:
    return await project_service.create_project(request)


@router.get("/project/{project_id}", response_model=Project)
async def get_project_endpoint(
    project_id: UUID,
    project_service: Annotated[Projects, Depends(get_projects_service)]
) -> Project:
    return await project_service.get_project(project_id)


@router.get("/projects", response_model=List[Project])
async def get_projects_endpoint(
    project_service: Annotated[Projects, Depends(get_projects_service)]
) -> List[Project]:
    return await project_service.get_projects()


@router.put("/project/{project_id}/view-port", response_model=Project)
async def update_project_view_port_endpoint(
    project_id: UUID,
    request: ProjectViewPortUpdate,
    project_service: Annotated[Projects, Depends(get_projects_service)]
) -> Project:
    return await project_service.update_project_view_port(project_id, request.view_port_x, request.view_port_y, request.zoom)
