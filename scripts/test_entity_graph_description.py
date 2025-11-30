#!/usr/bin/env python3
"""
Test script to create a realistic EntityGraph with all entity types,
edges, groups, root nodes, and nested groups, then print the description.
"""

from kvasir_ontology.graph.data_model import (
    EntityGraph,
    LeafNode,
    PipelineNode,
    BranchNode,
    EntityLinks,
    get_entity_graph_description,
)
import sys
from pathlib import Path
from uuid import uuid4
from datetime import datetime, timezone

# Add the ontology package to the path
sys.path.insert(0, str(Path(__file__).parent.parent / "ontology" / "src"))


def create_test_entity_graph() -> EntityGraph:
    """Create a comprehensive test EntityGraph with all entity types."""
    now = datetime.now(timezone.utc)

    # Generate UUIDs for all entities
    # Data sources
    ds1_id = uuid4()
    ds2_id = uuid4()
    ds1_node_id = uuid4()
    ds2_node_id = uuid4()

    # Datasets
    dset1_id = uuid4()
    dset2_id = uuid4()
    dset3_id = uuid4()
    dset1_node_id = uuid4()
    dset2_node_id = uuid4()
    dset3_node_id = uuid4()

    # Models
    model1_id = uuid4()
    model2_id = uuid4()
    model1_node_id = uuid4()
    model2_node_id = uuid4()

    # Pipelines
    pipeline1_id = uuid4()
    pipeline2_id = uuid4()
    pipeline1_node_id = uuid4()
    pipeline2_node_id = uuid4()

    # Pipeline runs
    run1_id = uuid4()
    run2_id = uuid4()
    run3_id = uuid4()
    run1_node_id = uuid4()
    run2_node_id = uuid4()
    run3_node_id = uuid4()

    # Analyses
    analysis1_id = uuid4()
    analysis2_id = uuid4()
    analysis1_node_id = uuid4()
    analysis2_node_id = uuid4()

    # Branch nodes (groups)
    group1_id = uuid4()  # Root group for data sources
    group2_id = uuid4()  # Root group for datasets
    group3_id = uuid4()  # Nested group inside group2
    group4_id = uuid4()  # Root group for pipelines
    group5_id = uuid4()  # Root group for models
    group6_id = uuid4()  # Root group for analyses

    # Create pipeline runs (these are LeafNodes)
    run1 = LeafNode(
        id=run1_node_id,
        name="Pipeline Run 1",
        description="First pipeline execution",
        node_type="leaf",
        x_position=100.0,
        y_position=200.0,
        entity_id=run1_id,
        entity_type="pipeline_run",
        created_at=now,
        updated_at=now,
        from_entities=EntityLinks(
            datasets=[dset1_node_id],
            models_instantiated=[model1_node_id],
        ),
        to_entities=EntityLinks(
            datasets=[dset2_node_id],
        ),
    )

    run2 = LeafNode(
        id=run2_node_id,
        name="Pipeline Run 2",
        description="Second pipeline execution",
        node_type="leaf",
        x_position=150.0,
        y_position=250.0,
        entity_id=run2_id,
        entity_type="pipeline_run",
        created_at=now,
        updated_at=now,
        from_entities=EntityLinks(
            datasets=[dset2_node_id],
            data_sources=[ds1_node_id],
        ),
        to_entities=EntityLinks(
            datasets=[dset3_node_id],
            models_instantiated=[model2_node_id],
        ),
    )

    run3 = LeafNode(
        id=run3_node_id,
        name="Pipeline Run 3",
        description="Third pipeline execution",
        node_type="leaf",
        x_position=200.0,
        y_position=300.0,
        entity_id=run3_id,
        entity_type="pipeline_run",
        created_at=now,
        updated_at=now,
        from_entities=EntityLinks(
            datasets=[dset3_node_id],
        ),
        to_entities=EntityLinks(
            data_sources=[ds2_node_id],
        ),
    )

    # Create data source nodes
    ds1 = LeafNode(
        id=ds1_node_id,
        name="PostgreSQL Database",
        description="Main production database",
        node_type="leaf",
        x_position=10.0,
        y_position=10.0,
        entity_id=ds1_id,
        entity_type="data_source",
        created_at=now,
        updated_at=now,
        from_entities=EntityLinks(),
        to_entities=EntityLinks(
            datasets=[dset1_node_id],
            pipelines=[pipeline1_node_id],
        ),
    )

    ds2 = LeafNode(
        id=ds2_node_id,
        name="S3 Bucket",
        description="Raw data storage",
        node_type="leaf",
        x_position=20.0,
        y_position=20.0,
        entity_id=ds2_id,
        entity_type="data_source",
        created_at=now,
        updated_at=now,
        from_entities=EntityLinks(
            pipeline_runs=[run3_node_id],
        ),
        to_entities=EntityLinks(
            datasets=[dset1_node_id],
            analyses=[analysis1_node_id],
        ),
    )

    # Create dataset nodes
    dset1 = LeafNode(
        id=dset1_node_id,
        name="Raw Customer Data",
        description="Initial customer dataset",
        node_type="leaf",
        x_position=50.0,
        y_position=50.0,
        entity_id=dset1_id,
        entity_type="dataset",
        created_at=now,
        updated_at=now,
        from_entities=EntityLinks(
            data_sources=[ds1_node_id, ds2_node_id],
        ),
        to_entities=EntityLinks(
            pipelines=[pipeline1_node_id, pipeline2_node_id],
            analyses=[analysis1_node_id],
            pipeline_runs=[run1_node_id],
        ),
    )

    dset2 = LeafNode(
        id=dset2_node_id,
        name="Processed Customer Data",
        description="Cleaned and transformed data",
        node_type="leaf",
        x_position=60.0,
        y_position=60.0,
        entity_id=dset2_id,
        entity_type="dataset",
        created_at=now,
        updated_at=now,
        from_entities=EntityLinks(
            pipeline_runs=[run1_node_id],
        ),
        to_entities=EntityLinks(
            pipelines=[pipeline2_node_id],
            analyses=[analysis2_node_id],
            pipeline_runs=[run2_node_id],
        ),
    )

    dset3 = LeafNode(
        id=dset3_node_id,
        name="Final Customer Data",
        description="Final processed dataset",
        node_type="leaf",
        x_position=70.0,
        y_position=70.0,
        entity_id=dset3_id,
        entity_type="dataset",
        created_at=now,
        updated_at=now,
        from_entities=EntityLinks(
            pipeline_runs=[run2_node_id],
        ),
        to_entities=EntityLinks(
            analyses=[analysis2_node_id],
            pipeline_runs=[run3_node_id],
        ),
    )

    # Create model nodes
    model1 = LeafNode(
        id=model1_node_id,
        name="Customer Churn Model",
        description="Predicts customer churn",
        node_type="leaf",
        x_position=200.0,
        y_position=50.0,
        entity_id=model1_id,
        entity_type="model_instantiated",
        created_at=now,
        updated_at=now,
        from_entities=EntityLinks(),
        to_entities=EntityLinks(
            pipelines=[pipeline1_node_id],
            analyses=[analysis1_node_id],
            pipeline_runs=[run1_node_id],
        ),
    )

    model2 = LeafNode(
        id=model2_node_id,
        name="Customer Lifetime Value Model",
        description="Predicts CLV",
        node_type="leaf",
        x_position=210.0,
        y_position=60.0,
        entity_id=model2_id,
        entity_type="model_instantiated",
        created_at=now,
        updated_at=now,
        from_entities=EntityLinks(
            pipeline_runs=[run2_node_id],
        ),
        to_entities=EntityLinks(
            pipelines=[pipeline2_node_id],
            analyses=[analysis2_node_id],
        ),
    )

    # Create pipeline nodes
    pipeline1 = PipelineNode(
        id=pipeline1_node_id,
        name="Data Processing Pipeline",
        description="Processes raw data",
        node_type="leaf",
        x_position=100.0,
        y_position=100.0,
        entity_id=pipeline1_id,
        entity_type="pipeline",
        created_at=now,
        updated_at=now,
        from_entities=EntityLinks(
            data_sources=[ds1_node_id],
            datasets=[dset1_node_id],
            models_instantiated=[model1_node_id],
        ),
        runs=[run1, run2],
    )

    pipeline2 = PipelineNode(
        id=pipeline2_node_id,
        name="Model Training Pipeline",
        description="Trains ML models",
        node_type="leaf",
        x_position=110.0,
        y_position=110.0,
        entity_id=pipeline2_id,
        entity_type="pipeline",
        created_at=now,
        updated_at=now,
        from_entities=EntityLinks(
            datasets=[dset1_node_id, dset2_node_id],
            models_instantiated=[model2_node_id],
        ),
        runs=[run3],
    )

    # Create analysis nodes
    analysis1 = LeafNode(
        id=analysis1_node_id,
        name="Churn Analysis",
        description="Analysis of customer churn",
        node_type="leaf",
        x_position=300.0,
        y_position=100.0,
        entity_id=analysis1_id,
        entity_type="analysis",
        created_at=now,
        updated_at=now,
        from_entities=EntityLinks(
            data_sources=[ds2_node_id],
            datasets=[dset1_node_id],
            models_instantiated=[model1_node_id],
        ),
        to_entities=EntityLinks(),
    )

    analysis2 = LeafNode(
        id=analysis2_node_id,
        name="CLV Analysis",
        description="Analysis of customer lifetime value",
        node_type="leaf",
        x_position=310.0,
        y_position=110.0,
        entity_id=analysis2_id,
        entity_type="analysis",
        created_at=now,
        updated_at=now,
        from_entities=EntityLinks(
            datasets=[dset2_node_id, dset3_node_id],
            models_instantiated=[model2_node_id],
        ),
        to_entities=EntityLinks(),
    )

    # Create nested group structure
    # Group 3 is nested inside Group 2
    group3 = BranchNode(
        id=group3_id,
        name="Processed Datasets",
        description="Group containing processed datasets",
        node_type="branch",
        x_position=0.0,
        y_position=0.0,
        created_at=now,
        updated_at=now,
        python_package_name="processed",
        children=[dset2, dset3],
    )

    # Group 2 contains dset1 and nested group3
    group2 = BranchNode(
        id=group2_id,
        name="Datasets Group",
        description="All datasets",
        node_type="branch",
        x_position=0.0,
        y_position=0.0,
        created_at=now,
        updated_at=now,
        python_package_name="datasets",
        children=[dset1, group3],
    )

    # Group 1 contains data sources
    group1 = BranchNode(
        id=group1_id,
        name="Data Sources Group",
        description="All data sources",
        node_type="branch",
        x_position=0.0,
        y_position=0.0,
        created_at=now,
        updated_at=now,
        python_package_name="data_sources",
        children=[ds1, ds2],
    )

    # Group 4 contains pipelines
    group4 = BranchNode(
        id=group4_id,
        name="Pipelines Group",
        description="All pipelines",
        node_type="branch",
        x_position=0.0,
        y_position=0.0,
        created_at=now,
        updated_at=now,
        python_package_name="pipelines",
        children=[pipeline1, pipeline2],
    )

    # Group 5 contains models
    group5 = BranchNode(
        id=group5_id,
        name="Models Group",
        description="All ML models",
        node_type="branch",
        x_position=0.0,
        y_position=0.0,
        created_at=now,
        updated_at=now,
        python_package_name="models",
        children=[model1, model2],
    )

    # Group 6 contains analyses
    group6 = BranchNode(
        id=group6_id,
        name="Analyses Group",
        description="All analyses",
        node_type="branch",
        x_position=0.0,
        y_position=0.0,
        created_at=now,
        updated_at=now,
        python_package_name="analyses",
        children=[analysis1, analysis2],
    )

    # Create the EntityGraph
    entity_graph = EntityGraph(
        data_sources=[group1],
        datasets=[group2],
        pipelines=[group4],
        models_instantiated=[group5],
        analyses=[group6],
    )

    return entity_graph


def main():
    """Create and print the entity graph description."""
    print("Creating comprehensive EntityGraph...")
    entity_graph = create_test_entity_graph()

    print("\n" + "="*80)
    print("Entity Graph Description (without positions):")
    print("="*80 + "\n")
    description = get_entity_graph_description(
        entity_graph, include_positions=False)
    print(description)

    print("\n" + "="*80)
    print("Entity Graph Description (with positions):")
    print("="*80 + "\n")
    description_with_pos = get_entity_graph_description(
        entity_graph, include_positions=True)
    print(description_with_pos)


if __name__ == "__main__":
    main()
