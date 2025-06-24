from typing import List
from uuid import UUID
from sqlalchemy import select, delete, insert, update
from synesis_api.database.service import execute, fetch_one, fetch_all
from synesis_api.modules.project.models import project, project_dataset, project_analysis, project_automation
from synesis_api.modules.project.schema import Project, ProjectCreate, ProjectUpdate


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


async def get_project(project_id: UUID) -> Project | None:
    # Get project details
    query = select(project).where(project.c.id == project_id)
    project_row = await fetch_one(query)

    if not project_row:
        return None

    # Get related IDs
    dataset_query = select(project_dataset.c.dataset_id).where(
        project_dataset.c.project_id == project_id)
    analysis_query = select(project_analysis.c.analysis_id).where(
        project_analysis.c.project_id == project_id)
    automation_query = select(project_automation.c.automation_id).where(
        project_automation.c.project_id == project_id)

    dataset_result = await fetch_all(dataset_query)
    analysis_result = await fetch_all(analysis_query)
    automation_result = await fetch_all(automation_query)

    return Project(
        id=project_row["id"],
        user_id=project_row["user_id"],
        name=project_row["name"],
        description=project_row["description"],
        created_at=project_row["created_at"],
        updated_at=project_row["updated_at"],
        dataset_ids=[row["dataset_id"] for row in dataset_result],
        analysis_ids=[row["analysis_id"] for row in analysis_result],
        automation_ids=[row["automation_id"] for row in automation_result]
    )


async def update_project(project_id: UUID, project_data: ProjectUpdate) -> Project | None:
    # Update project details if provided
    if project_data.name is not None or project_data.description is not None:
        update_values = {}
        if project_data.name is not None:
            update_values["name"] = project_data.name
        if project_data.description is not None:
            update_values["description"] = project_data.description

        query = update(project).where(
            project.c.id == project_id).values(**update_values)
        await execute(query, commit_after=True)

    # Update related ID if provided
    if project_data.type is not None and project_data.id is not None:
        if project_data.type == "dataset":
            if project_data.remove:
                # Delete existing relationship if it exists
                await execute(
                    delete(project_dataset).where(
                        project_dataset.c.project_id == project_id,
                        project_dataset.c.dataset_id == project_data.id
                    ),
                    commit_after=True
                )
            else:
                # Insert new relationship
                await execute(
                    insert(project_dataset).values(
                        project_id=project_id,
                        dataset_id=project_data.id
                    ),
                    commit_after=True
                )
        elif project_data.type == "analysis":
            if project_data.remove:
                await execute(
                    delete(project_analysis).where(
                        project_analysis.c.project_id == project_id,
                        project_analysis.c.analysis_id == project_data.id
                    ),
                    commit_after=True
                )
            else:
                await execute(
                    insert(project_analysis).values(
                        project_id=project_id,
                        analysis_id=project_data.id
                    ),
                    commit_after=True
                )
        elif project_data.type == "automation":
            if project_data.remove:
                await execute(
                    delete(project_automation).where(
                        project_automation.c.project_id == project_id,
                        project_automation.c.automation_id == project_data.id
                    ),
                    commit_after=True
                )
            else:
                await execute(
                    insert(project_automation).values(
                        project_id=project_id,
                        automation_id=project_data.id
                    ),
                    commit_after=True
                )

    return await get_project(project_id)


async def delete_project(project_id: UUID) -> bool:
    # Delete related records first
    await execute(delete(project_dataset).where(project_dataset.c.project_id == project_id), commit_after=True)
    await execute(delete(project_analysis).where(project_analysis.c.project_id == project_id), commit_after=True)
    await execute(delete(project_automation).where(project_automation.c.project_id == project_id), commit_after=True)

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
