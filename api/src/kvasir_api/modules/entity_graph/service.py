from uuid import UUID, uuid4
from datetime import datetime, timezone
from typing import List, Optional, Annotated, Union, Dict
from sqlalchemy import select, insert, delete, update, or_
from fastapi import Depends, HTTPException


from kvasir_api.database.service import fetch_all, execute, fetch_one
from kvasir_api.auth.service import get_current_user
from kvasir_api.auth.schema import User
from kvasir_api.modules.pipeline.service import Pipelines
from kvasir_ontology.graph.interface import GraphInterface
from kvasir_ontology.graph.data_model import (
    EntityGraph,
    EdgeBase,
    EdgeCreate,
    BranchNodeBase,
    BranchNodeCreate,
    LeafNodeCreate,
    LeafNode,
    LeafNodeBase,
    NodeBase,
    PipelineNode,
    ParentChildRelation,
    BranchNode,
    branch_node_to_entity_graph,
    EntityLinks,
    BRANCH_TYPE_LITERAL
)
from kvasir_api.modules.entity_graph.models import (
    node,
    branch_node,
    leaf_node,
    parent_child_relation,
    edge
)


class EntityGraphs(GraphInterface):

    def __init__(self, user_id: UUID):
        super().__init__(user_id)
        self.pipelines = Pipelines(user_id)

    async def add_nodes(self, nodes_create: List[Union[LeafNodeCreate, BranchNodeCreate]]) -> List[UUID]:
        nodes_data: List[NodeBase] = []
        leaf_nodes_data: List[LeafNodeBase] = []
        branch_nodes_data: List[BranchNodeBase] = []
        parent_child_data: List[ParentChildRelation] = []
        edges_data: List[EdgeBase] = []

        def _populate_data_recursive(node_create: Union[LeafNodeCreate, BranchNodeCreate], parent_ids: List[UUID]) -> None:
            node_base_obj = NodeBase(
                id=uuid4(),
                **node_create.model_dump(),
                node_type="leaf" if isinstance(
                    node_create, LeafNodeCreate) else "branch",
                created_at=datetime.now(timezone.utc),
                updated_at=datetime.now(timezone.utc)
            )

            nodes_data.append(node_base_obj)

            parent_child_data.extend([
                ParentChildRelation(
                    child_id=node_base_obj.id,
                    parent_id=parent_id,
                    created_at=datetime.now(timezone.utc),
                    updated_at=datetime.now(timezone.utc)
                ) for parent_id in parent_ids+(node_create.parent_branch_nodes or [])
            ])

            if isinstance(node_create, LeafNodeCreate):
                leaf_node_obj = LeafNodeBase(
                    id=node_base_obj.id,
                    **node_create.model_dump(),
                    created_at=datetime.now(timezone.utc),
                    updated_at=datetime.now(timezone.utc)
                )
                leaf_nodes_data.append(leaf_node_obj)

                edges_data.extend([EdgeBase(
                    from_entity_id=leaf_node_obj.entity_id,
                    to_entity_id=to_entity,
                    created_at=datetime.now(timezone.utc),
                    updated_at=datetime.now(timezone.utc)
                ) for to_entity in node_create.to_entities or []])

                edges_data.extend([EdgeBase(
                    from_entity_id=from_entity,
                    to_entity_id=leaf_node_obj.entity_id,
                    created_at=datetime.now(timezone.utc),
                    updated_at=datetime.now(timezone.utc)
                ) for from_entity in node_create.from_entities or []])

            else:
                branch_nodes_data.append(BranchNodeBase(
                    id=node_base_obj.id,
                    **node_create.model_dump(),
                    created_at=datetime.now(timezone.utc),
                    updated_at=datetime.now(timezone.utc)
                ))

                for child_node_create in node_create.children or []:
                    _populate_data_recursive(
                        child_node_create, parent_ids=[node_base_obj.id])

        for node_create in nodes_create:
            _populate_data_recursive(node_create, [])

        # Validate edge entity IDs before inserting
        if edges_data:
            # Collect all entity IDs that will be created in this batch
            entity_ids_in_batch = {
                leaf_node_obj.entity_id for leaf_node_obj in leaf_nodes_data}

            # Collect all entity IDs referenced in edges
            all_referenced_entity_ids = set()
            for edge_obj in edges_data:
                all_referenced_entity_ids.add(edge_obj.from_entity_id)
                all_referenced_entity_ids.add(edge_obj.to_entity_id)

            # Validate that all referenced entity IDs either exist in DB or are in this batch
            entity_ids_to_validate = all_referenced_entity_ids - entity_ids_in_batch
            if entity_ids_to_validate:
                await self._validate_entity_ids_exist(list(entity_ids_to_validate))

        if len(nodes_data):
            await execute(insert(node).values([obj.model_dump() for obj in nodes_data]), commit_after=True)
        if len(leaf_nodes_data):
            await execute(insert(leaf_node).values([obj.model_dump() for obj in leaf_nodes_data]), commit_after=True)
        if len(branch_nodes_data):
            await execute(insert(branch_node).values([obj.model_dump() for obj in branch_nodes_data]), commit_after=True)
        if len(parent_child_data):
            await execute(insert(parent_child_relation).values([obj.model_dump() for obj in parent_child_data]), commit_after=True)
        if len(edges_data):
            await execute(insert(edge).values([obj.model_dump() for obj in edges_data]), commit_after=True)

        return [node_base_obj.id for node_base_obj in nodes_data]

    async def get_node(self, node_id: UUID) -> Union[LeafNode, BranchNode]:
        found_nodes: Dict[UUID, Union[LeafNode, BranchNode]] = {}

        def _find_branch_type(children: List[Union[LeafNode, BranchNode]]) -> BRANCH_TYPE_LITERAL:
            found_types = set()
            for child in children:
                if child.node_type == "leaf":
                    found_types.add(child.entity_type)
                elif child.branch_type == "mixed":
                    return "mixed"
                else:
                    found_types.add(child.branch_type)

                if len(found_types) > 1:
                    return "mixed"

            return list(found_types)[0] if found_types else "mixed"

        async def _get_node_recursive(node_id: UUID) -> Union[LeafNode, BranchNode]:
            try:
                return found_nodes[node_id]
            except KeyError:
                node_query = (
                    select(
                        node.c.id,
                        node.c.name,
                        node.c.description,
                        node.c.node_type,
                        node.c.x_position,
                        node.c.y_position,
                        node.c.created_at,
                        node.c.updated_at,
                        leaf_node.c.entity_id,
                        leaf_node.c.entity_type,
                        branch_node.c.python_package_name
                    )
                    .outerjoin(leaf_node, node.c.id == leaf_node.c.id)
                    .outerjoin(branch_node, node.c.id == branch_node.c.id)
                    .where(node.c.id == node_id)
                )

                node_result = await fetch_one(node_query)

                if not node_result:
                    # print("NODE NOT FOUND"*10)
                    raise HTTPException(
                        status_code=404, detail="Node not found")

                parent_child_relations_query = select(
                    parent_child_relation.c.child_id,
                    parent_child_relation.c.parent_id
                ).where(or_(parent_child_relation.c.child_id == node_id, parent_child_relation.c.parent_id == node_id))

                parent_child_relations_result = await fetch_all(parent_child_relations_query)

                entity_id = node_result["entity_id"]
                edges_query = select(edge).where(
                    or_(edge.c.from_entity_id == entity_id, edge.c.to_entity_id == entity_id))
                edges_result = await fetch_all(edges_query)

                entity_type_query = select(leaf_node.c.entity_type, leaf_node.c.entity_id).where(leaf_node.c.entity_id.in_(
                    [e["from_entity_id"] for e in edges_result] + [e["to_entity_id"] for e in edges_result]))
                entity_type_result = await fetch_all(entity_type_query)
                entity_type_map = {e["entity_id"]: e["entity_type"]
                                   for e in entity_type_result}

                if node_result["node_type"] == "leaf":
                    entity_id = node_result["entity_id"]
                    from_entities = [
                        e["from_entity_id"] for e in edges_result if e["to_entity_id"] == entity_id]

                    if node_result["entity_type"] == "pipeline":
                        run_objs = await self.pipelines.get_pipeline_runs(
                            pipeline_ids=[entity_id])

                        # select node_id from leaf_node where entity_id in (select id from pipeline_run where pipeline_id = entity_id)
                        run_node_ids_query = select(leaf_node.c.id).where(leaf_node.c.entity_id.in_(
                            [run_obj.id for run_obj in run_objs]))
                        run_node_ids_result = await fetch_all(run_node_ids_query)
                        run_node_ids = [row["id"]
                                        for row in run_node_ids_result]
                        runs = [await _get_node_recursive(node_id) for node_id in run_node_ids]

                        out = PipelineNode(
                            **node_result,
                            from_entities=EntityLinks(
                                data_sources=[
                                    entity_id for entity_id in from_entities if entity_type_map[entity_id] == "data_source"],
                                datasets=[
                                    entity_id for entity_id in from_entities if entity_type_map[entity_id] == "dataset"],
                                analyses=[
                                    entity_id for entity_id in from_entities if entity_type_map[entity_id] == "analysis"],
                                pipelines=[
                                    entity_id for entity_id in from_entities if entity_type_map[entity_id] == "pipeline"],
                                models_instantiated=[
                                    entity_id for entity_id in from_entities if entity_type_map[entity_id] == "model_instantiated"]
                            ),
                            runs=runs
                        )
                    else:
                        to_entities = [
                            e["to_entity_id"] for e in edges_result if e["from_entity_id"] == entity_id]

                        out = LeafNode(
                            **node_result,
                            from_entities=EntityLinks(
                                data_sources=[
                                    entity_id for entity_id in from_entities if entity_type_map[entity_id] == "data_source"],
                                datasets=[
                                    entity_id for entity_id in from_entities if entity_type_map[entity_id] == "dataset"],
                                analyses=[
                                    entity_id for entity_id in from_entities if entity_type_map[entity_id] == "analysis"],
                                pipelines=[
                                    entity_id for entity_id in from_entities if entity_type_map[entity_id] == "pipeline"],
                                models_instantiated=[
                                    entity_id for entity_id in from_entities if entity_type_map[entity_id] == "model_instantiated"]
                            ),
                            to_entities=EntityLinks(
                                data_sources=[
                                    entity_id for entity_id in to_entities if entity_type_map[entity_id] == "data_source"],
                                datasets=[
                                    entity_id for entity_id in to_entities if entity_type_map[entity_id] == "dataset"],
                                analyses=[
                                    entity_id for entity_id in to_entities if entity_type_map[entity_id] == "analysis"],
                                pipelines=[
                                    entity_id for entity_id in to_entities if entity_type_map[entity_id] == "pipeline"],
                                models_instantiated=[
                                    entity_id for entity_id in to_entities if entity_type_map[entity_id] == "model_instantiated"]
                            )
                        )

                else:
                    child_ids = [
                        r["child_id"] for r in parent_child_relations_result if r["parent_id"] == node_id]
                    children = [await _get_node_recursive(cid) for cid in child_ids]

                    out = BranchNode(
                        **node_result,
                        children=children,
                        branch_type=_find_branch_type(children)
                    )

                found_nodes[node_id] = out

                return out

        return await _get_node_recursive(node_id)

    async def get_leaf_node_by_entity_id(self, entity_id: UUID) -> LeafNode:
        node_id = await fetch_one(select(leaf_node.c.id).where(leaf_node.c.entity_id == entity_id))
        if not node_id:
            raise HTTPException(status_code=404, detail="Leaf node not found")
        return await self.get_node(node_id["id"])

    async def delete_nodes(
        self,
        node_ids: Optional[List[UUID]] = None,
        entity_ids: Optional[List[UUID]] = None
    ) -> None:
        assert not (
            node_ids is None and entity_ids is None), "One of node_ids or entity_ids must be provided"

        node_ids = node_ids or []
        entity_ids = entity_ids or []

        leaf_nodes_query = select(leaf_node.c.entity_id, leaf_node.c.id).where(
            or_(leaf_node.c.id.in_(node_ids),
                leaf_node.c.entity_id.in_(entity_ids))
        )
        leaf_nodes_result = await fetch_all(leaf_nodes_query)

        node_ids += [row["id"] for row in leaf_nodes_result]
        entity_ids += [row["entity_id"] for row in leaf_nodes_result]
        node_ids = list(set(node_ids))
        entity_ids = list(set(entity_ids))

        if entity_ids:
            await execute(
                delete(edge).where(
                    or_(
                        edge.c.from_entity_id.in_(entity_ids),
                        edge.c.to_entity_id.in_(entity_ids)
                    )
                ),
                commit_after=True
            )

        await execute(
            delete(parent_child_relation).where(
                or_(
                    parent_child_relation.c.child_id.in_(node_ids),
                    parent_child_relation.c.parent_id.in_(node_ids)
                )
            ),
            commit_after=True
        )

        await execute(delete(leaf_node).where(leaf_node.c.id.in_(node_ids)), commit_after=True)
        await execute(delete(branch_node).where(branch_node.c.id.in_(node_ids)), commit_after=True)
        await execute(
            delete(node).where(node.c.id.in_(node_ids)),
            commit_after=True
        )

    async def update_node_position(self, node_id: UUID, x_position: float, y_position: float) -> None:
        await execute(
            update(node)
            .where(node.c.id == node_id)
            .values(x_position=x_position, y_position=y_position),
            commit_after=True
        )

    async def add_node_parents(self, child_ids: List[UUID], parent_ids: List[UUID]) -> None:
        assert len(child_ids) == len(
            parent_ids), "Must be equal number of nodes and parent, we map each child_id to the parent_id at the corresponding idx"

        parent_child_data = [
            ParentChildRelation(
                child_id=child_id,
                parent_id=parent_id,
                created_at=datetime.now(timezone.utc),
                updated_at=datetime.now(timezone.utc)
            ) for child_id, parent_id in zip(child_ids, parent_ids)
        ]

        await execute(insert(parent_child_relation).values([obj.model_dump() for obj in parent_child_data]), commit_after=True)

    async def remove_node_parents(self, child_ids: List[UUID], parent_ids: List[UUID]) -> None:
        assert len(child_ids) == len(
            parent_ids), "Must be equal number of children and parents, we map each child_id to the parent_id at the corresponding idx"

        if not child_ids:
            return

        conditions = [
            (parent_child_relation.c.child_id == child_id) &
            (parent_child_relation.c.parent_id == parent_id)
            for child_id, parent_id in zip(child_ids, parent_ids)
        ]

        await execute(
            delete(parent_child_relation).where(or_(*conditions)),
            commit_after=True
        )

    async def _validate_entity_ids_exist(self, entity_ids: List[UUID]) -> None:
        if not entity_ids:
            return

        existing_entities_query = select(leaf_node.c.entity_id).where(
            leaf_node.c.entity_id.in_(entity_ids)
        )
        existing_entities_result = await fetch_all(existing_entities_query)
        existing_entity_ids = {row["entity_id"]
                               for row in existing_entities_result}

        invalid_entity_ids = set(entity_ids) - existing_entity_ids
        if invalid_entity_ids:
            raise HTTPException(
                status_code=400,
                detail=f"Invalid entity IDs: {sorted(invalid_entity_ids)}. These entities do not exist in the entity graph."
            )

    async def create_edges(self, edges_create: List[EdgeCreate]) -> None:
        if not edges_create:
            return

        all_entity_ids = [e.from_entity_id for e in edges_create] + \
            [e.to_entity_id for e in edges_create]
        await self._validate_entity_ids_exist(all_entity_ids)

        conditions = [
            (edge.c.from_entity_id == e.from_entity_id) &
            (edge.c.to_entity_id == e.to_entity_id)
            for e in edges_create
        ]
        existing_edges_query = select(edge.c.from_entity_id, edge.c.to_entity_id).where(
            or_(*conditions) if conditions else False
        )
        existing_edges_result = await fetch_all(existing_edges_query)
        existing_edges_set = {
            (row["from_entity_id"], row["to_entity_id"])
            for row in existing_edges_result
        }

        new_edges_data = [
            EdgeBase(
                **e.model_dump(),
                created_at=datetime.now(timezone.utc),
                updated_at=datetime.now(timezone.utc)
            ) for e in edges_create
            if (e.from_entity_id, e.to_entity_id) not in existing_edges_set
        ]

        if new_edges_data:
            await execute(insert(edge).values([obj.model_dump() for obj in new_edges_data]), commit_after=True)

    async def remove_entity_edges(self, entity_id: UUID) -> None:
        await execute(
            delete(edge).where(
                or_(
                    edge.c.from_entity_id == entity_id,
                    edge.c.to_entity_id == entity_id
                )
            ),
            commit_after=True
        )

    async def remove_edges(
        self,
        from_entities: List[UUID],
        to_entities: List[UUID]
    ) -> None:

        conditions = [
            (edge.c.from_entity_id == from_entity) &
            (edge.c.to_entity_id == to_entity)
            for from_entity, to_entity in zip(from_entities, to_entities)
        ]

        await execute(
            delete(edge).where(or_(*conditions)),
            commit_after=True
        )

    async def get_entity_graph(self, root_node_id: UUID) -> EntityGraph:
        node_obj = await self.get_node(root_node_id)
        return branch_node_to_entity_graph(node_obj)

    async def get_node_leaves(self, node_id: UUID) -> List[LeafNode]:
        node_obj = await self.get_node(node_id)

        def _get_node_leaves_recursive(node_obj: Union[LeafNode, BranchNode]) -> List[LeafNode]:
            if node_obj.node_type == "leaf":
                return [node_obj]
            else:
                return [leaf for child in node_obj.children for leaf in _get_node_leaves_recursive(child)]

        return _get_node_leaves_recursive(node_obj)


# For dependency injection
async def get_graph_service(user: Annotated[User, Depends(get_current_user)]) -> GraphInterface:
    return EntityGraphs(user.id)
