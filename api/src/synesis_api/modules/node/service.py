from typing import List, Literal, Optional
from uuid import UUID, uuid4
from sqlalchemy import select, insert, update, delete, func
from synesis_api.database.service import execute, fetch_one, fetch_all
from synesis_api.modules.node.models import node, data_source_node, dataset_node, analysis_node, automation_node
from synesis_api.modules.node.schema import FrontendNode, FrontendNodeCreate


BASE_X_POSITIONS = {
    "data_source": 0,
    "dataset": 250,
    "analysis": 500,
    "automation": 750
}
VERTICAL_SPACING = 75


async def _create_node_position(project_id: UUID, node_type: Literal["data_source", "dataset", "analysis", "automation"]):
    lowest_y_position = await fetch_one(select(func.min(node.c.y_position).label("min_y")).where(node.c.project_id == project_id, node.c.type == node_type))

    if lowest_y_position and lowest_y_position["min_y"] is not None:
        return BASE_X_POSITIONS[node_type], lowest_y_position["min_y"] + VERTICAL_SPACING
    else:
        return BASE_X_POSITIONS[node_type], 0


async def create_node(frontend_node: FrontendNodeCreate) -> FrontendNode:

    # First create the base node

    if frontend_node.x_position is None or frontend_node.y_position is None:
        x_position, y_position = await _create_node_position(frontend_node.project_id, frontend_node.type)
    else:
        x_position = frontend_node.x_position
        y_position = frontend_node.y_position

    id = uuid4()
    node_query = insert(node).values(
        id=id,
        project_id=frontend_node.project_id,
        x_position=x_position,
        y_position=y_position,
        type=frontend_node.type
    )

    await execute(node_query, commit_after=True)

    # Then create the specific node type
    if frontend_node.type == "data_source":
        specific_node_query = insert(data_source_node).values(
            id=id,
            data_source_id=frontend_node.data_source_id
        )
    elif frontend_node.type == "dataset":
        specific_node_query = insert(dataset_node).values(
            id=id,
            dataset_id=frontend_node.dataset_id
        )
    elif frontend_node.type == "analysis":
        specific_node_query = insert(analysis_node).values(
            id=id,
            analysis_id=frontend_node.analysis_id
        )
    elif frontend_node.type == "automation":
        specific_node_query = insert(automation_node).values(
            id=id,
            automation_id=frontend_node.automation_id
        )

    await execute(specific_node_query, commit_after=True)

    # Return the created FrontendNode
    return FrontendNode(
        id=id,
        project_id=frontend_node.project_id,
        x_position=x_position,
        y_position=y_position,
        type=frontend_node.type,
        data_source_id=frontend_node.data_source_id,
        dataset_id=frontend_node.dataset_id,
        analysis_id=frontend_node.analysis_id,
        automation_id=frontend_node.automation_id
    )


async def get_node(node_id: UUID) -> Optional[FrontendNode]:
    query = select(node).where(node.c.id == node_id)
    node_row = await fetch_one(query)

    if not node_row:
        return None

    # Check if it's a data source node
    data_source_query = select(data_source_node).where(
        data_source_node.c.id == node_id)
    data_source_row = await fetch_one(data_source_query)
    if data_source_row:
        return FrontendNode(
            id=node_row["id"],
            project_id=node_row["project_id"],
            x_position=node_row["x_position"],
            y_position=node_row["y_position"],
            type="data_source",
            data_source_id=data_source_row["data_source_id"],
            dataset_id=None,
            analysis_id=None,
            automation_id=None
        )

    # Check if it's a dataset node
    dataset_query = select(dataset_node).where(dataset_node.c.id == node_id)
    dataset_row = await fetch_one(dataset_query)
    if dataset_row:
        return FrontendNode(
            id=node_row["id"],
            project_id=node_row["project_id"],
            x_position=node_row["x_position"],
            y_position=node_row["y_position"],
            type="dataset",
            dataset_id=dataset_row["dataset_id"],
            analysis_id=None,
            automation_id=None
        )

    # Check if it's an analysis node
    analysis_query = select(analysis_node).where(analysis_node.c.id == node_id)
    analysis_row = await fetch_one(analysis_query)
    if analysis_row:
        return FrontendNode(
            id=node_row["id"],
            project_id=node_row["project_id"],
            x_position=node_row["x_position"],
            y_position=node_row["y_position"],
            type="analysis",
            dataset_id=None,
            analysis_id=analysis_row["analysis_id"],
            automation_id=None
        )

    # Check if it's an automation node
    automation_query = select(automation_node).where(
        automation_node.c.id == node_id)
    automation_row = await fetch_one(automation_query)
    if automation_row:
        return FrontendNode(
            id=node_row["id"],
            project_id=node_row["project_id"],
            x_position=node_row["x_position"],
            y_position=node_row["y_position"],
            type="automation",
            dataset_id=None,
            analysis_id=None,
            automation_id=automation_row["automation_id"]
        )

    return None


async def get_project_nodes(project_id: UUID) -> List[FrontendNode]:
    # Get all nodes for the project
    query = select(node).where(node.c.project_id == project_id)
    nodes = await fetch_all(query)

    result = []
    for node_row in nodes:
        # Check each node type
        data_source_query = select(data_source_node).where(
            data_source_node.c.id == node_row["id"])
        data_source_row = await fetch_one(data_source_query)
        if data_source_row:
            result.append(FrontendNode(
                id=node_row["id"],
                project_id=node_row["project_id"],
                x_position=node_row["x_position"],
                y_position=node_row["y_position"],
                type="data_source",
                data_source_id=data_source_row["data_source_id"],
                dataset_id=None,
                analysis_id=None,
                automation_id=None
            ))
            continue

        dataset_query = select(dataset_node).where(
            dataset_node.c.id == node_row["id"])
        dataset_row = await fetch_one(dataset_query)
        if dataset_row:
            result.append(FrontendNode(
                id=node_row["id"],
                project_id=node_row["project_id"],
                x_position=node_row["x_position"],
                y_position=node_row["y_position"],
                type="dataset",
                dataset_id=dataset_row["dataset_id"],
                analysis_id=None,
                automation_id=None
            ))
            continue

        analysis_query = select(analysis_node).where(
            analysis_node.c.id == node_row["id"])
        analysis_row = await fetch_one(analysis_query)
        if analysis_row:
            result.append(FrontendNode(
                id=node_row["id"],
                project_id=node_row["project_id"],
                x_position=node_row["x_position"],
                y_position=node_row["y_position"],
                type="analysis",
                dataset_id=None,
                analysis_id=analysis_row["analysis_id"],
                automation_id=None
            ))
            continue

        automation_query = select(automation_node).where(
            automation_node.c.id == node_row["id"])
        automation_row = await fetch_one(automation_query)
        if automation_row:
            result.append(FrontendNode(
                id=node_row["id"],
                project_id=node_row["project_id"],
                x_position=node_row["x_position"],
                y_position=node_row["y_position"],
                type="automation",
                dataset_id=None,
                analysis_id=None,
                automation_id=automation_row["automation_id"]
            ))
            continue

    return result


async def update_node_position(frontend_node: FrontendNode) -> Optional[FrontendNode]:
    query = update(node).where(node.c.id == frontend_node.id).values(
        x_position=frontend_node.x_position,
        y_position=frontend_node.y_position
    ).returning(node)

    node_row = await fetch_one(query, commit_after=True)
    if not node_row:
        return None

    return frontend_node


async def delete_node(node_id: UUID) -> bool:
    # Delete from the specific node type table first
    data_source_query = delete(data_source_node).where(
        data_source_node.c.id == node_id)
    await execute(data_source_query, commit_after=True)

    dataset_query = delete(dataset_node).where(dataset_node.c.id == node_id)
    await execute(dataset_query, commit_after=True)

    analysis_query = delete(analysis_node).where(analysis_node.c.id == node_id)
    await execute(analysis_query, commit_after=True)

    automation_query = delete(automation_node).where(
        automation_node.c.id == node_id)
    await execute(automation_query, commit_after=True)

    # Then delete from the base node table
    query = delete(node).where(node.c.id == node_id)
    result = await execute(query, commit_after=True)

    return result.rowcount > 0
