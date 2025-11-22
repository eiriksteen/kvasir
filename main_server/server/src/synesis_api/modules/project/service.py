import uuid
import re
import asyncio
from datetime import datetime, timezone
from typing import List, Optional, Annotated
from sqlalchemy import select, insert, update
from fastapi import HTTPException, Depends

from synesis_api.auth.service import get_current_user
from synesis_api.auth.schema import User
from synesis_api.database.service import fetch_all, execute, fetch_one
from synesis_api.modules.project.models import project
from synesis_api.modules.project.schema import (
    ProjectCreate,
    Project,
)
from synesis_api.modules.entity_graph.service import EntityGraphs
from kvasir_ontology.graph.data_model import NodeGroupCreate
from kvasir_research.sandbox.modal import ModalSandbox


def _to_snake_case(name: str) -> str:
    """Convert a string to snake_case."""
    # Replace spaces and hyphens with underscores
    s1 = re.sub(r'[\s\-]+', '_', name)
    # Insert underscore before uppercase letters and convert to lowercase
    s2 = re.sub('(.)([A-Z][a-z]+)', r'\1_\2', s1)
    s3 = re.sub('([a-z0-9])([A-Z])', r'\1_\2', s2)
    # Remove any non-alphanumeric characters except underscores
    s4 = re.sub(r'[^\w]', '', s3)
    # Convert to lowercase and remove duplicate underscores
    return re.sub(r'_+', '_', s4.lower()).strip('_')


class Projects:
    def __init__(self, user_id: uuid.UUID):
        self.user_id = user_id
        self.graph_service = EntityGraphs(user_id)

    async def create_project(self, project_create: ProjectCreate) -> Project:
        mount_group_id = project_create.mount_group_id
        name_snake_case = _to_snake_case(project_create.name)

        # Create a node group if mount_group_id is not provided
        if mount_group_id is None:
            node_group = await self.graph_service.create_node_group(
                NodeGroupCreate(
                    name=name_snake_case,
                    description=project_create.description,
                    python_package_name=name_snake_case
                )
            )
            project_create.mount_group_id = node_group.id

        project_record = Project(
            id=project_create.mount_group_id,
            user_id=self.user_id,
            **project_create.model_dump(),
            view_port_x=0.0,
            view_port_y=0.0,
            view_port_zoom=1.0,
            created_at=datetime.now(timezone.utc),
            updated_at=datetime.now(timezone.utc)
        )

        # Run the init to get the project setup
        # Need to force_build on project creation to ensure the package is installed
        sb = ModalSandbox(project_create.mount_group_id, name_snake_case)
        await sb.create_container_if_not_exists(force_build=True)

        await execute(
            insert(project).values(project_record.model_dump()),
            commit_after=True
        )

        return project_record

    async def get_project(self, project_id: uuid.UUID) -> Project:
        """Get a single project by ID."""
        projects = await self.get_projects([project_id])
        if not projects:
            raise HTTPException(
                status_code=404,
                detail=f"Project with id {project_id} not found"
            )
        return projects[0]

    async def get_projects(self, project_ids: Optional[List[uuid.UUID]] = None) -> List[Project]:
        query = select(project).where(project.c.user_id == self.user_id)

        if project_ids:
            query = query.where(project.c.id.in_(project_ids))

        records = await fetch_all(query)

        if not records:
            return []

        return [Project(**record) for record in records]

    async def update_project_view_port(self, project_id: uuid.UUID, view_port_x: float, view_port_y: float, zoom: float) -> Project:
        await self.get_project(project_id)

        await execute(
            update(project)
            .where(project.c.id == project_id)
            .where(project.c.user_id == self.user_id)
            .values(
                view_port_x=view_port_x,
                view_port_y=view_port_y,
                view_port_zoom=zoom,
                updated_at=datetime.now(timezone.utc)
            ),
            commit_after=True
        )

        updated_record = await fetch_one(
            select(project).where(project.c.id == project_id)
        )
        if not updated_record:
            raise HTTPException(
                status_code=404,
                detail=f"Project with id {project_id} not found after update"
            )
        return Project(**updated_record)


async def get_projects_service(
    user: Annotated[User, Depends(get_current_user)]
) -> Projects:
    """Dependency injection for Projects service."""
    return Projects(user.id)
