import uuid
from typing import List, Optional, Annotated
from datetime import datetime, timezone
from sqlalchemy import select, insert, delete, and_, update
from fastapi import HTTPException, Depends

from synesis_api.database.service import execute, fetch_all, fetch_one
from synesis_api.auth.service import get_current_user
from synesis_api.auth.schema import User
from kvasir_ontology.graph.interface import GraphInterface
from kvasir_ontology.graph.data_model import (
    EntityGraph,
    EdgeDefinition,
    NodeGroupBase,
    NodeGroupCreate,
    EntityNodeCreate,
    EntityNode,
    EntityNodeBase,
    EdgePoints,
    PipelineNode,
    NodeInGroup,
)
from synesis_api.modules.entity_graph.models import (
    entity_node,
    node_group,
    node_in_group,
    dataset_from_data_source,
    data_source_supported_in_pipeline,
    dataset_supported_in_pipeline,
    model_instantiated_supported_in_pipeline,
    dataset_in_pipeline_run,
    data_source_in_pipeline_run,
    model_instantiated_in_pipeline_run,
    pipeline_run_output_dataset,
    pipeline_run_output_model_entity,
    pipeline_run_output_data_source,
    dataset_in_analysis,
    data_source_in_analysis,
    model_instantiated_in_analysis,
)
from synesis_api.modules.pipeline.models import pipeline_run


# =============================================================================
# Edge Management Constants
# =============================================================================

VALID_EDGES = {
    ("data_source", "dataset"): dataset_from_data_source,
    ("data_source", "pipeline"): data_source_supported_in_pipeline,
    ("data_source", "analysis"): data_source_in_analysis,
    ("dataset", "pipeline"): dataset_supported_in_pipeline,
    ("dataset", "analysis"): dataset_in_analysis,
    ("model_instantiated", "pipeline"): model_instantiated_supported_in_pipeline,
    ("model_instantiated", "analysis"): model_instantiated_in_analysis,
}

PIPELINE_RUN_EDGE_TABLES = {
    ("dataset", "pipeline_run"): (dataset_in_pipeline_run, "input"),
    ("data_source", "pipeline_run"): (data_source_in_pipeline_run, "input"),
    ("model_instantiated", "pipeline_run"): (model_instantiated_in_pipeline_run, "input"),
    ("pipeline_run", "dataset"): (pipeline_run_output_dataset, "output"),
    ("pipeline_run", "model_instantiated"): (pipeline_run_output_model_entity, "output"),
    ("pipeline_run", "data_source"): (pipeline_run_output_data_source, "output"),
}


# =============================================================================
# Graph Service Implementation
# =============================================================================

class EntityGraphs(GraphInterface):

    def __init__(self, user_id: uuid.UUID):
        super().__init__(user_id)

    async def add_node(self, node: EntityNodeCreate) -> EntityNode:
        existing = await fetch_one(
            select(entity_node).where(entity_node.c.id == node.id)
        )
        if existing:
            raise HTTPException(
                status_code=409,
                detail=f"Node {node.id} already exists"
            )

        timestamp = datetime.now(timezone.utc)

        # Create and validate Pydantic model
        node_base = EntityNodeBase(
            **node.model_dump(),
            created_at=timestamp,
            updated_at=timestamp,
        )

        await execute(
            insert(entity_node).values(node_base.model_dump()),
            commit_after=True
        )

        if node.node_groups:
            for group_id in node.node_groups:
                await self.add_node_to_group(node.id, group_id)

        return await self.get_node(node.id)

    async def add_nodes(self, nodes: List[EntityNodeCreate]) -> List[EntityNode]:
        if not nodes:
            return []

        node_ids = [node.id for node in nodes]
        existing_nodes = await fetch_all(
            select(entity_node).where(entity_node.c.id.in_(node_ids))
        )
        if existing_nodes:
            existing_ids = {record["id"] for record in existing_nodes}
            raise HTTPException(
                status_code=409,
                detail=f"Nodes already exist: {existing_ids}"
            )

        timestamp = datetime.now(timezone.utc)

        node_bases = [
            EntityNodeBase(
                id=node.id,
                name=node.name,
                entity_type=node.entity_type,
                x_position=node.x_position,
                y_position=node.y_position,
                created_at=timestamp,
                updated_at=timestamp,
            )
            for node in nodes
        ]

        await execute(
            insert(entity_node).values([n.model_dump() for n in node_bases]),
            commit_after=True
        )

        node_group_mappings = []
        for node in nodes:
            if node.node_groups:
                for group_id in node.node_groups:
                    node_group_mapping = NodeInGroup(
                        node_id=node.id,
                        node_group_id=group_id,
                        created_at=timestamp,
                        updated_at=timestamp,
                    )
                    node_group_mappings.append(node_group_mapping.model_dump())

        if node_group_mappings:
            await execute(
                insert(node_in_group).values(node_group_mappings),
                commit_after=True
            )

        return await self.get_nodes(node_ids)

    async def get_node(self, node_id: uuid.UUID) -> EntityNode:
        node_record = await fetch_one(
            select(entity_node).where(entity_node.c.id == node_id)
        )
        if not node_record:
            raise HTTPException(
                status_code=404,
                detail=f"Node {node_id} not found"
            )

        edges = await self.get_node_edges(node_id)
        from_entities = EdgePoints()
        to_entities = EdgePoints()

        for edge in edges:
            if edge.from_node_id == node_id:
                if edge.to_node_type == "data_source":
                    to_entities.data_sources.append(edge.to_node_id)
                elif edge.to_node_type == "dataset":
                    to_entities.datasets.append(edge.to_node_id)
                elif edge.to_node_type == "pipeline":
                    to_entities.pipelines.append(edge.to_node_id)
                elif edge.to_node_type == "model_instantiated":
                    to_entities.models_instantiated.append(edge.to_node_id)
                elif edge.to_node_type == "analysis":
                    to_entities.analyses.append(edge.to_node_id)
                elif edge.to_node_type == "pipeline_run":
                    to_entities.pipeline_runs.append(edge.to_node_id)
            elif edge.to_node_id == node_id:
                # This node is the destination
                if edge.from_node_type == "data_source":
                    from_entities.data_sources.append(edge.from_node_id)
                elif edge.from_node_type == "dataset":
                    from_entities.datasets.append(edge.from_node_id)
                elif edge.from_node_type == "pipeline":
                    from_entities.pipelines.append(edge.from_node_id)
                elif edge.from_node_type == "model_instantiated":
                    from_entities.models_instantiated.append(
                        edge.from_node_id)
                elif edge.from_node_type == "analysis":
                    from_entities.analyses.append(edge.from_node_id)
                elif edge.from_node_type == "pipeline_run":
                    from_entities.pipeline_runs.append(edge.from_node_id)

        return EntityNode(
            id=node_record["id"],
            name=node_record["name"],
            description=node_record.get("description"),
            x_position=node_record["x_position"],
            y_position=node_record["y_position"],
            from_entities=from_entities,
            to_entities=to_entities,
        )

    async def get_nodes(self, node_ids: List[uuid.UUID]) -> List[EntityNode]:
        if not node_ids:
            return []

        node_records = await fetch_all(
            select(entity_node).where(entity_node.c.id.in_(node_ids))
        )

        if not node_records:
            return []

        found_ids = {record["id"] for record in node_records}
        missing_ids = set(node_ids) - found_ids
        if missing_ids:
            raise HTTPException(
                status_code=404,
                detail=f"Nodes not found: {missing_ids}"
            )

        nodes_by_type: dict[str, List[dict]] = {
            "data_source": [],
            "dataset": [],
            "pipeline": [],
            "model_instantiated": [],
            "analysis": [],
            "pipeline_run": [],
        }

        for record in node_records:
            entity_type = record["entity_type"]
            if entity_type in nodes_by_type:
                nodes_by_type[entity_type].append(dict(record))

        # Build nodes for each type (excluding pipeline which needs special handling)
        all_nodes: List[EntityNode] = []

        for entity_type in ["data_source", "dataset", "model_instantiated", "analysis", "pipeline_run"]:
            if nodes_by_type[entity_type]:
                type_nodes = await self._get_nodes_from_records(nodes_by_type[entity_type])
                all_nodes.extend(type_nodes)

        # Handle pipeline nodes separately if needed
        if nodes_by_type["pipeline"]:
            pipeline_nodes = await self._get_pipeline_nodes_from_records(nodes_by_type["pipeline"])
            # Convert PipelineNode to EntityNode for consistency
            for pnode in pipeline_nodes:
                all_nodes.append(EntityNode(
                    id=pnode.id,
                    name=pnode.name,
                    description=pnode.description,
                    x_position=pnode.x_position,
                    y_position=pnode.y_position,
                    from_entities=pnode.from_entities,
                    to_entities=EdgePoints(),  # Pipeline outputs go through runs
                ))

        # Maintain original order
        node_map = {node.id: node for node in all_nodes}
        return [node_map[node_id] for node_id in node_ids if node_id in node_map]

    async def update_node_position(self, node_id: uuid.UUID, x_position: float, y_position: float) -> EntityNode:
        await execute(
            update(entity_node).where(entity_node.c.id == node_id).values(
                x_position=x_position, y_position=y_position),
            commit_after=True
        )
        return await self.get_node(node_id)

    async def delete_node(self, node_id: uuid.UUID) -> None:
        node_record = await fetch_one(
            select(entity_node).where(entity_node.c.id == node_id)
        )
        if not node_record:
            raise HTTPException(
                status_code=404,
                detail=f"Node {node_id} not found"
            )

        await execute(
            delete(node_in_group).where(node_in_group.c.node_id == node_id),
            commit_after=True
        )

        await execute(
            delete(entity_node).where(entity_node.c.id == node_id),
            commit_after=True
        )

    async def get_node_edges(self, node_id: uuid.UUID) -> List[EdgeDefinition]:
        edges: List[EdgeDefinition] = []

        node_record = await fetch_one(
            select(entity_node).where(entity_node.c.id == node_id)
        )
        if not node_record:
            raise HTTPException(
                status_code=404,
                detail=f"Node {node_id} not found"
            )

        entity_type = node_record["entity_type"]

        for (from_type, to_type), table in VALID_EDGES.items():
            from_field = f"{from_type}_id"
            to_field = f"{to_type}_id"

            if from_type == entity_type:
                records = await fetch_all(
                    select(table).where(
                        getattr(table.c, from_field) == node_id)
                )
                for record in records:
                    edges.append(EdgeDefinition(
                        from_node_type=from_type,
                        from_node_id=node_id,
                        to_node_type=to_type,
                        to_node_id=record[to_field]
                    ))

            if to_type == entity_type:
                records = await fetch_all(
                    select(table).where(getattr(table.c, to_field) == node_id)
                )
                for record in records:
                    edges.append(EdgeDefinition(
                        from_node_type=from_type,
                        from_node_id=record[from_field],
                        to_node_type=to_type,
                        to_node_id=node_id
                    ))

        for (from_type, to_type), (table, direction) in PIPELINE_RUN_EDGE_TABLES.items():
            if direction == "input" and from_type == entity_type:
                # Node is an input to pipeline runs
                entity_field = f"{entity_type}_id"
                records = await fetch_all(
                    select(table).where(
                        getattr(table.c, entity_field) == node_id)
                )
                for record in records:
                    edges.append(EdgeDefinition(
                        from_node_type=from_type,
                        from_node_id=node_id,
                        to_node_type="pipeline_run",
                        to_node_id=record["pipeline_run_id"]
                    ))

            elif direction == "output" and to_type == entity_type:
                # Node is an output from pipeline runs
                entity_field = f"{entity_type}_id"
                records = await fetch_all(
                    select(table).where(
                        getattr(table.c, entity_field) == node_id)
                )
                for record in records:
                    edges.append(EdgeDefinition(
                        from_node_type="pipeline_run",
                        from_node_id=record["pipeline_run_id"],
                        to_node_type=to_type,
                        to_node_id=node_id
                    ))

        return edges

    async def get_node_groups(
        self,
        node_id: Optional[uuid.UUID] = None,
        group_ids: Optional[List[uuid.UUID]] = None
    ) -> List[NodeGroupBase]:
        if not node_id and not group_ids:
            raise HTTPException(
                status_code=400,
                detail="Either node_id or group_ids must be provided"
            )

        if node_id and group_ids:
            raise HTTPException(
                status_code=400,
                detail="Only one of node_id or group_ids should be provided"
            )

        if node_id:
            # Get all groups the node belongs to
            node_group_records = await fetch_all(
                select(node_in_group).where(node_in_group.c.node_id == node_id)
            )

            if not node_group_records:
                return []

            group_ids = [record["node_group_id"]
                         for record in node_group_records]

        # Fetch groups by IDs
        group_records = await fetch_all(
            select(node_group).where(node_group.c.id.in_(group_ids))
        )

        return [
            NodeGroupBase(**record)
            for record in group_records
        ]

    async def get_node_group(self, node_group_id: uuid.UUID) -> NodeGroupBase:
        group_record = await fetch_one(
            select(node_group).where(node_group.c.id == node_group_id)
        )
        if not group_record:
            raise HTTPException(
                status_code=404,
                detail=f"Node group {node_group_id} not found"
            )

        return NodeGroupBase(**group_record)

    async def create_node_group(self, node_group_create: NodeGroupCreate) -> NodeGroupBase:
        group_id = uuid.uuid4()
        timestamp = datetime.now(timezone.utc)

        node_group_record = NodeGroupBase(
            id=group_id,
            **node_group_create.model_dump(),
            created_at=timestamp,
            updated_at=timestamp,
        )

        await execute(
            insert(node_group).values(node_group_record.model_dump()),
            commit_after=True
        )

        return node_group_record

    async def delete_node_group(self, node_group_id: uuid.UUID) -> None:
        group_record = await fetch_one(
            select(node_group).where(node_group.c.id == node_group_id)
        )
        if not group_record:
            raise HTTPException(
                status_code=404,
                detail=f"Node group {node_group_id} not found"
            )

        await execute(
            delete(node_in_group).where(
                node_in_group.c.node_group_id == node_group_id),
            commit_after=True
        )

        await execute(
            delete(node_group).where(node_group.c.id == node_group_id),
            commit_after=True
        )

    async def add_node_to_group(self, node_id: uuid.UUID, node_group_id: uuid.UUID) -> None:
        node_record = await fetch_one(
            select(entity_node).where(entity_node.c.id == node_id)
        )
        if not node_record:
            raise HTTPException(
                status_code=404,
                detail=f"Node {node_id} not found"
            )

        group_record = await fetch_one(
            select(node_group).where(node_group.c.id == node_group_id)
        )
        if not group_record:
            raise HTTPException(
                status_code=404,
                detail=f"Node group {node_group_id} not found"
            )

        existing = await fetch_one(
            select(node_in_group).where(
                and_(
                    node_in_group.c.node_id == node_id,
                    node_in_group.c.node_group_id == node_group_id
                )
            )
        )
        if existing:
            return

        timestamp = datetime.now(timezone.utc)
        await execute(
            insert(node_in_group).values({
                "node_id": node_id,
                "node_group_id": node_group_id,
                "created_at": timestamp,
                "updated_at": timestamp,
            }),
            commit_after=True
        )

    async def remove_nodes_from_groups(
        self, node_ids: List[uuid.UUID], node_group_ids: List[uuid.UUID]
    ) -> None:
        if not node_ids or not node_group_ids:
            return

        await execute(
            delete(node_in_group).where(
                and_(
                    node_in_group.c.node_id.in_(node_ids),
                    node_in_group.c.node_group_id.in_(node_group_ids)
                )
            ),
            commit_after=True
        )

    async def create_edges(self, edges: List[EdgeDefinition]) -> None:
        timestamp = datetime.now(timezone.utc)

        for edge in edges:
            key = (edge.from_node_type, edge.to_node_type)

            is_pipeline_run_input = (
                edge.to_node_type == "pipeline_run" and key in PIPELINE_RUN_EDGE_TABLES
            )
            is_pipeline_run_output = (
                edge.from_node_type == "pipeline_run" and key in PIPELINE_RUN_EDGE_TABLES
            )

            if is_pipeline_run_input or is_pipeline_run_output:
                table, _ = PIPELINE_RUN_EDGE_TABLES[key]
            elif key in VALID_EDGES:
                table = VALID_EDGES[key]
            else:
                raise HTTPException(
                    status_code=400,
                    detail=(
                        f"Invalid edge: {edge.from_node_type} -> {edge.to_node_type}\n\n"
                        f"Valid edges: {list(VALID_EDGES.keys())}"
                    ),
                )

            value = {"created_at": timestamp, "updated_at": timestamp}

            if is_pipeline_run_input:
                value["pipeline_run_id"] = edge.to_node_id
                if edge.from_node_type == "data_source":
                    value["data_source_id"] = edge.from_node_id
                elif edge.from_node_type == "dataset":
                    value["dataset_id"] = edge.from_node_id
                elif edge.from_node_type == "model_instantiated":
                    value["model_instantiated_id"] = edge.from_node_id

            elif is_pipeline_run_output:
                value["pipeline_run_id"] = edge.from_node_id
                if edge.to_node_type == "data_source":
                    value["data_source_id"] = edge.to_node_id
                elif edge.to_node_type == "dataset":
                    value["dataset_id"] = edge.to_node_id
                elif edge.to_node_type == "model_instantiated":
                    value["model_instantiated_id"] = edge.to_node_id

            else:
                if edge.from_node_type == "pipeline":
                    value["pipeline_id"] = edge.from_node_id
                elif edge.from_node_type == "data_source":
                    value["data_source_id"] = edge.from_node_id
                elif edge.from_node_type == "dataset":
                    value["dataset_id"] = edge.from_node_id
                elif edge.from_node_type == "model_instantiated":
                    value["model_instantiated_id"] = edge.from_node_id
                elif edge.from_node_type == "analysis":
                    value["analysis_id"] = edge.from_node_id

                if edge.to_node_type == "pipeline":
                    value["pipeline_id"] = edge.to_node_id
                elif edge.to_node_type == "data_source":
                    value["data_source_id"] = edge.to_node_id
                elif edge.to_node_type == "dataset":
                    value["dataset_id"] = edge.to_node_id
                elif edge.to_node_type == "model_instantiated":
                    value["model_instantiated_id"] = edge.to_node_id
                elif edge.to_node_type == "analysis":
                    value["analysis_id"] = edge.to_node_id

            await execute(insert(table).values(value), commit_after=True)

    async def remove_edges(self, edges: List[EdgeDefinition]) -> None:
        for edge in edges:
            key = (edge.from_node_type, edge.to_node_type)

            is_pipeline_run_input = (
                edge.to_node_type == "pipeline_run" and key in PIPELINE_RUN_EDGE_TABLES
            )
            is_pipeline_run_output = (
                edge.from_node_type == "pipeline_run" and key in PIPELINE_RUN_EDGE_TABLES
            )

            if is_pipeline_run_input or is_pipeline_run_output:
                table, _ = PIPELINE_RUN_EDGE_TABLES[key]
            elif key in VALID_EDGES:
                table = VALID_EDGES[key]
            else:
                raise HTTPException(
                    status_code=400,
                    detail=f"Invalid edge: {edge.from_node_type} -> {edge.to_node_type}. Valid edges: {list(VALID_EDGES.keys())}",
                )

            conditions = []

            if is_pipeline_run_input:
                conditions.append(table.c.pipeline_run_id == edge.to_node_id)
                if edge.from_node_type == "data_source":
                    conditions.append(
                        table.c.data_source_id == edge.from_node_id)
                elif edge.from_node_type == "dataset":
                    conditions.append(table.c.dataset_id == edge.from_node_id)
                elif edge.from_node_type == "model_instantiated":
                    conditions.append(
                        table.c.model_instantiated_id == edge.from_node_id)

            elif is_pipeline_run_output:
                conditions.append(table.c.pipeline_run_id == edge.from_node_id)
                if edge.to_node_type == "data_source":
                    conditions.append(
                        table.c.data_source_id == edge.to_node_id)
                elif edge.to_node_type == "dataset":
                    conditions.append(table.c.dataset_id == edge.to_node_id)
                elif edge.to_node_type == "model_instantiated":
                    conditions.append(
                        table.c.model_instantiated_id == edge.to_node_id)

            else:
                if edge.from_node_type == "pipeline":
                    conditions.append(table.c.pipeline_id == edge.from_node_id)
                elif edge.from_node_type == "data_source":
                    conditions.append(
                        table.c.data_source_id == edge.from_node_id)
                elif edge.from_node_type == "dataset":
                    conditions.append(table.c.dataset_id == edge.from_node_id)
                elif edge.from_node_type == "model_instantiated":
                    conditions.append(
                        table.c.model_instantiated_id == edge.from_node_id)
                elif edge.from_node_type == "analysis":
                    conditions.append(table.c.analysis_id == edge.from_node_id)

                if edge.to_node_type == "pipeline":
                    conditions.append(table.c.pipeline_id == edge.to_node_id)
                elif edge.to_node_type == "data_source":
                    conditions.append(
                        table.c.data_source_id == edge.to_node_id)
                elif edge.to_node_type == "dataset":
                    conditions.append(table.c.dataset_id == edge.to_node_id)
                elif edge.to_node_type == "model_instantiated":
                    conditions.append(
                        table.c.model_instantiated_id == edge.to_node_id)
                elif edge.to_node_type == "analysis":
                    conditions.append(table.c.analysis_id == edge.to_node_id)

            await execute(delete(table).where(and_(*conditions)), commit_after=True)

    async def get_entity_graph(
        self,
        root_group_id: Optional[uuid.UUID] = None,
        root_node_id: Optional[uuid.UUID] = None,
    ) -> EntityGraph:
        if not root_group_id and not root_node_id:
            raise HTTPException(
                status_code=400,
                detail="Either root_group_id or root_node_id must be provided"
            )

        node_ids: List[uuid.UUID] = []
        if root_group_id:
            node_group_records = await fetch_all(
                select(node_in_group).where(
                    node_in_group.c.node_group_id == root_group_id
                )
            )
            node_ids = [record["node_id"] for record in node_group_records]
        elif root_node_id:
            node_ids = [root_node_id]

        if not node_ids:
            return EntityGraph()

        node_records = await fetch_all(
            select(entity_node).where(entity_node.c.id.in_(node_ids))
        )

        # Group nodes by entity type
        nodes_by_type: dict[str, List[dict]] = {
            "data_source": [],
            "dataset": [],
            "pipeline": [],
            "model_instantiated": [],
            "analysis": [],
        }

        for record in node_records:
            entity_type = record["entity_type"]
            if entity_type in nodes_by_type:
                nodes_by_type[entity_type].append(dict(record))

        # Build graph nodes directly from entity_node records
        data_sources_in_graph = await self._get_nodes_from_records(nodes_by_type["data_source"])
        datasets_in_graph = await self._get_nodes_from_records(nodes_by_type["dataset"])
        pipelines_in_graph = await self._get_pipeline_nodes_from_records(nodes_by_type["pipeline"])
        models_instantiated_in_graph = await self._get_nodes_from_records(nodes_by_type["model_instantiated"])
        analyses_in_graph = await self._get_nodes_from_records(nodes_by_type["analysis"])

        return EntityGraph(
            data_sources=data_sources_in_graph,
            datasets=datasets_in_graph,
            pipelines=pipelines_in_graph,
            analyses=analyses_in_graph,
            models_instantiated=models_instantiated_in_graph,
        )

    async def _get_nodes_from_records(
        self, node_records: List[dict]
    ) -> List[EntityNode]:
        """
        Build EntityNode objects from entity_node table records with their edges.
        """
        if not node_records:
            return []

        entity_ids = [record["id"] for record in node_records]
        entity_type = node_records[0]["entity_type"] if node_records else None

        if not entity_type:
            return []

        # Build edge maps
        from_entities_map = {entity_id: EdgePoints()
                             for entity_id in entity_ids}
        to_entities_map = {entity_id: EdgePoints() for entity_id in entity_ids}

        # Fetch edges from VALID_EDGES tables
        for (from_type, to_type), table in VALID_EDGES.items():
            if from_type == entity_type:
                from_field = f"{from_type}_id"
                to_field = f"{to_type}_id"
                records = await fetch_all(
                    select(table).where(
                        getattr(table.c, from_field).in_(entity_ids))
                )
                for record in records:
                    entity_id = record[from_field]
                    target_id = record[to_field]
                    to_entities = to_entities_map[entity_id]
                    if to_type == "data_source":
                        to_entities.data_sources.append(target_id)
                    elif to_type == "dataset":
                        to_entities.datasets.append(target_id)
                    elif to_type == "pipeline":
                        to_entities.pipelines.append(target_id)
                    elif to_type == "model_instantiated":
                        to_entities.models_instantiated.append(target_id)
                    elif to_type == "analysis":
                        to_entities.analyses.append(target_id)

            elif to_type == entity_type:
                from_field = f"{from_type}_id"
                to_field = f"{to_type}_id"
                records = await fetch_all(
                    select(table).where(
                        getattr(table.c, to_field).in_(entity_ids))
                )
                for record in records:
                    entity_id = record[to_field]
                    source_id = record[from_field]
                    from_entities = from_entities_map[entity_id]
                    if from_type == "data_source":
                        from_entities.data_sources.append(source_id)
                    elif from_type == "dataset":
                        from_entities.datasets.append(source_id)
                    elif from_type == "pipeline":
                        from_entities.pipelines.append(source_id)
                    elif from_type == "model_instantiated":
                        from_entities.models_instantiated.append(source_id)
                    elif from_type == "analysis":
                        from_entities.analyses.append(source_id)

        # Fetch edges from PIPELINE_RUN_EDGE_TABLES
        for (from_type, to_type), (table, direction) in PIPELINE_RUN_EDGE_TABLES.items():
            if direction == "input" and from_type == entity_type:
                entity_field = f"{entity_type}_id"
                records = await fetch_all(
                    select(table).where(
                        getattr(table.c, entity_field).in_(entity_ids))
                )
                for record in records:
                    entity_id = record[entity_field]
                    run_id = record["pipeline_run_id"]
                    to_entities_map[entity_id].pipeline_runs.append(run_id)

            elif direction == "output" and to_type == entity_type:
                entity_field = f"{entity_type}_id"
                records = await fetch_all(
                    select(table).where(
                        getattr(table.c, entity_field).in_(entity_ids))
                )
                for record in records:
                    entity_id = record[entity_field]
                    run_id = record["pipeline_run_id"]
                    from_entities_map[entity_id].pipeline_runs.append(run_id)

        # Build EntityNode objects from records
        nodes = []
        for record in node_records:
            entity_id = record["id"]
            nodes.append(EntityNode(
                id=entity_id,
                name=record["name"],
                description=record.get("description"),
                x_position=record["x_position"],
                y_position=record["y_position"],
                from_entities=from_entities_map[entity_id],
                to_entities=to_entities_map[entity_id]
            ))

        return nodes

    async def _get_pipeline_nodes_from_records(
        self, node_records: List[dict]
    ) -> List[PipelineNode]:
        """
        Build PipelineNode objects from entity_node table records with their runs nested.
        """
        if not node_records:
            return []

        entity_ids = [record["id"] for record in node_records]

        # Build edge maps for pipelines
        from_entities_map = {entity_id: EdgePoints()
                             for entity_id in entity_ids}
        to_entities_map = {entity_id: EdgePoints() for entity_id in entity_ids}

        # Fetch edges from VALID_EDGES tables for pipelines
        for (from_type, to_type), table in VALID_EDGES.items():
            if from_type == "pipeline":
                records = await fetch_all(
                    select(table).where(table.c.pipeline_id.in_(entity_ids))
                )
                for record in records:
                    entity_id = record["pipeline_id"]
                    target_id = record[f"{to_type}_id"]
                    to_entities = to_entities_map[entity_id]
                    if to_type == "data_source":
                        to_entities.data_sources.append(target_id)
                    elif to_type == "dataset":
                        to_entities.datasets.append(target_id)
                    elif to_type == "model_instantiated":
                        to_entities.models_instantiated.append(target_id)
                    elif to_type == "analysis":
                        to_entities.analyses.append(target_id)

            elif to_type == "pipeline":
                records = await fetch_all(
                    select(table).where(table.c.pipeline_id.in_(entity_ids))
                )
                for record in records:
                    entity_id = record["pipeline_id"]
                    source_id = record[f"{from_type}_id"]
                    from_entities = from_entities_map[entity_id]
                    if from_type == "data_source":
                        from_entities.data_sources.append(source_id)
                    elif from_type == "dataset":
                        from_entities.datasets.append(source_id)
                    elif from_type == "model_instantiated":
                        from_entities.models_instantiated.append(source_id)
                    elif from_type == "analysis":
                        from_entities.analyses.append(source_id)

        # Fetch pipeline runs for all pipelines
        run_records = await fetch_all(
            select(pipeline_run).where(
                pipeline_run.c.pipeline_id.in_(entity_ids))
        )

        # Group runs by pipeline_id
        runs_by_pipeline: dict[uuid.UUID, List[dict]] = {
            pid: [] for pid in entity_ids}
        for run_record in run_records:
            runs_by_pipeline[run_record["pipeline_id"]].append(
                dict(run_record))

        # Build pipeline run nodes for all runs
        run_nodes_by_pipeline: dict[uuid.UUID, List[EntityNode]] = {}
        for pipeline_id, runs in runs_by_pipeline.items():
            if runs:
                run_nodes_by_pipeline[pipeline_id] = await self._get_pipeline_run_nodes(runs)
            else:
                run_nodes_by_pipeline[pipeline_id] = []

        # Build PipelineNode objects
        nodes = []
        for record in node_records:
            entity_id = record["id"]
            nodes.append(PipelineNode(
                id=entity_id,
                name=record["name"],
                description=record.get("description"),
                x_position=record["x_position"],
                y_position=record["y_position"],
                from_entities=from_entities_map[entity_id],
                runs=run_nodes_by_pipeline[entity_id]
            ))

        return nodes

    async def _get_pipeline_run_nodes(
        self, run_records: List[dict]
    ) -> List[EntityNode]:
        """
        Build EntityNode objects for pipeline runs with their edges.
        """
        if not run_records:
            return []

        run_ids = [record["id"] for record in run_records]

        # Build edge maps for runs
        from_entities_map = {run_id: EdgePoints() for run_id in run_ids}
        to_entities_map = {run_id: EdgePoints() for run_id in run_ids}

        # Fetch input edges (entities going into pipeline runs)
        for (from_type, to_type), (table, direction) in PIPELINE_RUN_EDGE_TABLES.items():
            if direction == "input" and to_type == "pipeline_run":
                records = await fetch_all(
                    select(table).where(table.c.pipeline_run_id.in_(run_ids))
                )
                for record in records:
                    run_id = record["pipeline_run_id"]
                    from_entities = from_entities_map[run_id]
                    if from_type == "data_source":
                        from_entities.data_sources.append(
                            record["data_source_id"])
                    elif from_type == "dataset":
                        from_entities.datasets.append(record["dataset_id"])
                    elif from_type == "model_instantiated":
                        from_entities.models_instantiated.append(
                            record["model_instantiated_id"])

            elif direction == "output" and from_type == "pipeline_run":
                records = await fetch_all(
                    select(table).where(table.c.pipeline_run_id.in_(run_ids))
                )
                for record in records:
                    run_id = record["pipeline_run_id"]
                    to_entities = to_entities_map[run_id]
                    if to_type == "data_source":
                        to_entities.data_sources.append(
                            record["data_source_id"])
                    elif to_type == "dataset":
                        to_entities.datasets.append(record["dataset_id"])
                    elif to_type == "model_instantiated":
                        to_entities.models_instantiated.append(
                            record["model_instantiated_id"])

        # Build EntityNode objects for runs
        run_nodes = []
        for record in run_records:
            run_id = record["id"]
            run_nodes.append(EntityNode(
                id=run_id,
                name=record["name"],
                description=record.get("description", ""),
                x_position=0.0,  # Pipeline runs don't have positions in entity_node table
                y_position=0.0,
                from_entities=from_entities_map[run_id],
                to_entities=to_entities_map[run_id]
            ))

        return run_nodes


# For dependency injection
async def get_graph_service(user: Annotated[User, Depends(get_current_user)]) -> GraphInterface:
    return EntityGraphs(user.id)
