from uuid import UUID, uuid4
from typing import List, Literal, Optional, Dict, Any
from sqlalchemy import select, insert, update, delete, func

from synesis_api.database.service import execute, fetch_one, fetch_all
from synesis_api.modules.node.models import node, data_source_node, dataset_node, analysis_node, pipeline_node, model_node, model_source_node
from synesis_schemas.main_server import FrontendNode, FrontendNodeCreate


NODE_TYPE_TABLES = {
    "data_source": data_source_node,
    "model_source": model_source_node,
    "dataset": dataset_node,
    "analysis": analysis_node,
    "pipeline": pipeline_node,
    "model": model_node
}

NODE_TYPE_ID_FIELDS = {
    "data_source": "data_source_id",
    "model_source": "model_source_id",
    "dataset": "dataset_id",
    "analysis": "analysis_id",
    "pipeline": "pipeline_id",
    "model": "model_id"
}


BASE_X_POSITIONS = {
    "data_source": 0,
    "model_source": 100,
    "dataset": 200,
    "analysis": 300,
    "pipeline": 400,
    "model": 500
}
VERTICAL_SPACING = 100


def _build_frontend_node(node_row: Dict[str, Any], node_type: str, specific_id: Optional[UUID] = None) -> FrontendNode:
    """Build a FrontendNode from base node data and specific node data."""
    return FrontendNode(
        id=node_row["id"],
        project_id=node_row["project_id"],
        x_position=node_row["x_position"],
        y_position=node_row["y_position"],
        type=node_type,
        data_source_id=specific_id if node_type == "data_source" else None,
        model_source_id=specific_id if node_type == "model_source" else None,
        dataset_id=specific_id if node_type == "dataset" else None,
        analysis_id=specific_id if node_type == "analysis" else None,
        pipeline_id=specific_id if node_type == "pipeline" else None,
        model_id=specific_id if node_type == "model" else None
    )


async def _create_node_position(project_id: UUID, node_type: Literal["data_source", "model_source", "dataset", "analysis", "pipeline", "model"]):
    max_y_position = await fetch_one(select(func.max(node.c.y_position).label("max_y")).where(node.c.project_id == project_id, node.c.type == node_type))

    if max_y_position and max_y_position["max_y"] is not None:
        return BASE_X_POSITIONS[node_type], max_y_position["max_y"] + VERTICAL_SPACING
    else:
        return BASE_X_POSITIONS[node_type], 0


async def create_node(frontend_node: FrontendNodeCreate) -> FrontendNode:

    # First create the base node

    if frontend_node.x_position is None or frontend_node.y_position is None:
        x_position, y_position = await _create_node_position(frontend_node.project_id, frontend_node.type)
    else:
        x_position, y_position = frontend_node.x_position, frontend_node.y_position

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
    node_type = frontend_node.type
    table = NODE_TYPE_TABLES[node_type]
    id_field = NODE_TYPE_ID_FIELDS[node_type]
    specific_id = getattr(frontend_node, id_field)

    specific_node_query = insert(table).values(
        id=id,
        **{id_field: specific_id}
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
        model_source_id=frontend_node.model_source_id,
        dataset_id=frontend_node.dataset_id,
        analysis_id=frontend_node.analysis_id,
        pipeline_id=frontend_node.pipeline_id,
        model_id=frontend_node.model_id
    )


async def get_node(node_id: UUID) -> Optional[FrontendNode]:
    # Single query with LEFT JOINs to get node data
    query = select(
        node.c.id,
        node.c.project_id,
        node.c.x_position,
        node.c.y_position,
        node.c.type,
        data_source_node.c.data_source_id,
        dataset_node.c.dataset_id,
        analysis_node.c.analysis_id,
        pipeline_node.c.pipeline_id,
        model_node.c.model_id
    ).select_from(
        node
        .outerjoin(data_source_node, node.c.id == data_source_node.c.id)
        .outerjoin(dataset_node, node.c.id == dataset_node.c.id)
        .outerjoin(analysis_node, node.c.id == analysis_node.c.id)
        .outerjoin(pipeline_node, node.c.id == pipeline_node.c.id)
        .outerjoin(model_node, node.c.id == model_node.c.id)
    ).where(node.c.id == node_id)

    row = await fetch_one(query)

    if not row:
        return None

    # Get the specific ID based on node type
    specific_id = row[NODE_TYPE_ID_FIELDS[row["type"]]]
    return _build_frontend_node(row, row["type"], specific_id)


async def get_project_nodes(project_id: UUID) -> List[FrontendNode]:
    # Single query with LEFT JOINs to get all node data at once
    query = select(
        node.c.id,
        node.c.project_id,
        node.c.x_position,
        node.c.y_position,
        node.c.type,
        data_source_node.c.data_source_id,
        model_source_node.c.model_source_id,
        dataset_node.c.dataset_id,
        analysis_node.c.analysis_id,
        pipeline_node.c.pipeline_id,
        model_node.c.model_id
    ).select_from(
        node
        .outerjoin(data_source_node, node.c.id == data_source_node.c.id)
        .outerjoin(model_source_node, node.c.id == model_source_node.c.id)
        .outerjoin(dataset_node, node.c.id == dataset_node.c.id)
        .outerjoin(analysis_node, node.c.id == analysis_node.c.id)
        .outerjoin(pipeline_node, node.c.id == pipeline_node.c.id)
        .outerjoin(model_node, node.c.id == model_node.c.id)
    ).where(node.c.project_id == project_id)

    rows = await fetch_all(query)

    result = []
    for row in rows:
        # Get the specific ID based on node type
        specific_id = row[NODE_TYPE_ID_FIELDS[row["type"]]]
        result.append(_build_frontend_node(
            row, row["type"], specific_id))

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
    # Delete from all specific node type tables first (foreign key constraints)
    for table in NODE_TYPE_TABLES.values():
        query = delete(table).where(table.c.id == node_id)
        await execute(query, commit_after=True)

    # Then delete from the base node table
    query = delete(node).where(node.c.id == node_id)
    result = await execute(query, commit_after=True)

    return result.rowcount > 0
