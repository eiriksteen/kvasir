"""
Test script to simulate add_nodes without DB calls.
Prints the final pydantic models before model_dump.
"""
import json
from uuid import UUID, uuid4
from datetime import datetime, timezone
from typing import List, Union

from kvasir_ontology.graph.data_model import (
    EdgeBase,
    BranchNodeBase,
    BranchNodeCreate,
    LeafNodeCreate,
    LeafNodeBase,
    NodeBase,
    ParentChildRelation,
)


def simulate_add_nodes(nodes_create: List[Union[LeafNodeCreate, BranchNodeCreate]]) -> List[UUID]:
    """
    Simulates add_nodes logic without database calls.
    Prints all final pydantic models before model_dump.
    """
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
            ) for parent_id in parent_ids + (node_create.parent_branch_nodes or [])
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

    # Print all models before model_dump
    print("=" * 80)
    print("NODES DATA")
    print("=" * 80)
    for i, node in enumerate(nodes_data):
        print(f"\nNode {i + 1}:")
        print(json.dumps(node.model_dump(mode='json'), indent=2, default=str))

    print("\n" + "=" * 80)
    print("LEAF NODES DATA")
    print("=" * 80)
    for i, leaf_node in enumerate(leaf_nodes_data):
        print(f"\nLeaf Node {i + 1}:")
        print(json.dumps(leaf_node.model_dump(mode='json'), indent=2, default=str))

    print("\n" + "=" * 80)
    print("BRANCH NODES DATA")
    print("=" * 80)
    for i, branch_node in enumerate(branch_nodes_data):
        print(f"\nBranch Node {i + 1}:")
        print(json.dumps(branch_node.model_dump(
            mode='json'), indent=2, default=str))

    print("\n" + "=" * 80)
    print("PARENT-CHILD RELATIONS DATA")
    print("=" * 80)
    for i, relation in enumerate(parent_child_data):
        print(f"\nRelation {i + 1}:")
        print(json.dumps(relation.model_dump(mode='json'), indent=2, default=str))

    print("\n" + "=" * 80)
    print("EDGES DATA")
    print("=" * 80)
    for i, edge in enumerate(edges_data):
        print(f"\nEdge {i + 1}:")
        print(json.dumps(edge.model_dump(mode='json'), indent=2, default=str))

    print("\n" + "=" * 80)
    print("SUMMARY")
    print("=" * 80)
    print(f"Total nodes: {len(nodes_data)}")
    print(f"Total leaf nodes: {len(leaf_nodes_data)}")
    print(f"Total branch nodes: {len(branch_nodes_data)}")
    print(f"Total parent-child relations: {len(parent_child_data)}")
    print(f"Total edges: {len(edges_data)}")
    print(f"Returned node IDs: {[str(node.id) for node in nodes_data]}")

    return [node_base_obj.id for node_base_obj in nodes_data]


if __name__ == "__main__":
    # Example usage
    from uuid import uuid4 as gen_uuid

    # Create some test data
    entity_id_1 = gen_uuid()
    entity_id_2 = gen_uuid()
    entity_id_3 = gen_uuid()
    entity_id_4 = gen_uuid()

    # Example 1: Simple leaf node
    leaf_node_1 = LeafNodeCreate(
        entity_id=entity_id_1,
        name="Test Leaf Node 1",
        entity_type="dataset",
        x_position=100.0,
        y_position=200.0,
        description="A test leaf node",
        from_entities=[entity_id_2],
        to_entities=[entity_id_3]
    )

    # Example 2: Branch node with children
    child_leaf_1 = LeafNodeCreate(
        entity_id=entity_id_2,
        name="Child Leaf 1",
        entity_type="data_source",
        x_position=150.0,
        y_position=250.0
    )

    child_leaf_2 = LeafNodeCreate(
        entity_id=entity_id_3,
        name="Child Leaf 2",
        entity_type="dataset",
        x_position=200.0,
        y_position=300.0,
        to_entities=[entity_id_4]
    )

    branch_node_1 = BranchNodeCreate(
        name="Test Branch Node",
        x_position=300.0,
        y_position=400.0,
        description="A test branch node with children",
        children=[child_leaf_1, child_leaf_2]
    )

    # Run simulation
    print("Running add_nodes simulation...\n")
    node_ids = simulate_add_nodes([leaf_node_1, branch_node_1])
    print(f"\nSimulation complete. Generated {len(node_ids)} node IDs.")
