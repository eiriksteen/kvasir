from typing import List
from uuid import UUID

from project_server.client import ProjectClient
from synesis_schemas.main_server import (
    ProjectCreate,
    Project,
    ProjectDetailsUpdate,
    AddEntityToProject,
    RemoveEntityFromProject
)


async def post_create_project(client: ProjectClient, project_data: ProjectCreate) -> Project:
    """Create a new project"""
    response = await client.send_request("post", "/project/create-project", json=project_data.model_dump(mode="json"))
    return Project(**response.body)


async def get_project(client: ProjectClient, project_id: UUID) -> Project:
    """Get a project by ID"""
    response = await client.send_request("get", f"/project/get-project/{project_id}")
    return Project(**response.body)


async def put_update_project(client: ProjectClient, project_id: UUID, project_data: ProjectDetailsUpdate) -> Project:
    """Update project details (name/description)"""
    response = await client.send_request("put", f"/project/update-project/{project_id}", json=project_data.model_dump(mode="json"))
    return Project(**response.body)


async def post_add_entity(client: ProjectClient, entity_data: AddEntityToProject) -> Project:
    """Add an entity (data source, dataset, analysis, pipeline) to a project"""
    response = await client.send_request("post", f"/project/add-entity", json=entity_data.model_dump(mode="json"))
    return Project(**response.body)


async def delete_entity(client: ProjectClient, entity_data: RemoveEntityFromProject) -> Project:
    """Remove an entity (data source, dataset, analysis, pipeline) from a project"""
    response = await client.send_request("delete", f"/project/remove-entity", json=entity_data.model_dump(mode="json"))
    return Project(**response.body)


async def delete_project(client: ProjectClient, project_id: UUID) -> dict:
    """Delete a project"""
    response = await client.send_request("delete", f"/project/delete-project/{project_id}")
    return response.body


async def get_user_projects(client: ProjectClient) -> List[Project]:
    """Get all projects for the current user"""
    response = await client.send_request("get", "/project/get-user-projects")
    return [Project(**project) for project in response.body]
