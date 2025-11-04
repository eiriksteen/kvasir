import uuid
from typing import List
from datetime import datetime, timezone
from sqlalchemy import select, insert, delete, and_
from fastapi import HTTPException

from synesis_api.database.service import fetch_all, execute
from synesis_api.modules.data_sources.service import get_user_data_sources
from synesis_api.modules.data_objects.service import get_user_datasets
from synesis_api.modules.pipeline.service import get_user_pipelines
from synesis_api.modules.model.service import get_user_model_entities
from synesis_api.modules.analysis.service import get_user_analyses
from synesis_api.modules.entity_graph._description_utils import (
    get_data_source_description,
    get_dataset_description,
    get_pipeline_description,
    get_model_entity_description,
    get_analysis_description,
)
from synesis_api.modules.entity_graph.models import (
    dataset_from_data_source,
    data_source_supported_in_pipeline,
    dataset_supported_in_pipeline,
    model_entity_supported_in_pipeline,
    dataset_in_pipeline_run,
    data_source_in_pipeline_run,
    model_entity_in_pipeline_run,
    pipeline_run_output_dataset,
    pipeline_run_output_model_entity,
    pipeline_run_output_data_source,
    dataset_in_analysis,
    data_source_in_analysis,
    model_entity_in_analysis,
)
from synesis_schemas.main_server import (
    EntityGraph,
    GraphNode,
    PipelineGraphNode,
    DataSource,
    Dataset,
    Pipeline,
    ModelEntity,
    Analysis,
    EdgePoints,
    EdgesCreate,
    PipelineRunInDB,
    EntityGraphUsingNames,
    EntityDetail,
    EntityDetailsResponse,
)


# =============================================================================
# Edge Management
# =============================================================================

VALID_EDGES = {
    ("data_source", "dataset"): dataset_from_data_source,
    ("data_source", "pipeline"): data_source_supported_in_pipeline,
    ("data_source", "analysis"): data_source_in_analysis,
    ("dataset", "pipeline"): dataset_supported_in_pipeline,
    ("dataset", "analysis"): dataset_in_analysis,
    ("model_entity", "pipeline"): model_entity_supported_in_pipeline,
    ("model_entity", "analysis"): model_entity_in_analysis,
}

PIPELINE_RUN_EDGE_TABLES = {
    ("dataset", "pipeline_run"): (dataset_in_pipeline_run, "input"),
    ("data_source", "pipeline_run"): (data_source_in_pipeline_run, "input"),
    ("model_entity", "pipeline_run"): (model_entity_in_pipeline_run, "input"),
    ("pipeline_run", "dataset"): (pipeline_run_output_dataset, "output"),
    ("pipeline_run", "model_entity"): (pipeline_run_output_model_entity, "output"),
    ("pipeline_run", "data_source"): (pipeline_run_output_data_source, "output"),
}


async def create_edges(edges: EdgesCreate) -> None:
    timestamp = datetime.now(timezone.utc)

    for edge in edges.edges:
        key = (edge.from_node_type, edge.to_node_type)

        # Check if this is a pipeline run edge (input to or output from a run)
        is_pipeline_run_input = edge.to_node_type == "pipeline_run" and key in PIPELINE_RUN_EDGE_TABLES
        is_pipeline_run_output = edge.from_node_type == "pipeline_run" and key in PIPELINE_RUN_EDGE_TABLES

        if is_pipeline_run_input or is_pipeline_run_output:
            table, _ = PIPELINE_RUN_EDGE_TABLES[key]
        elif key in VALID_EDGES:
            table = VALID_EDGES[key]
        else:
            raise HTTPException(
                status_code=400,
                detail=f"Invalid edge: {edge.from_node_type} -> {edge.to_node_type}"
            )

        value = {"created_at": timestamp, "updated_at": timestamp}

        # Handle pipeline run edges specially
        if is_pipeline_run_input:
            # Entity is an input to a pipeline run
            value["pipeline_run_id"] = edge.to_node_id
            if edge.from_node_type == "data_source":
                value["data_source_id"] = edge.from_node_id
            elif edge.from_node_type == "dataset":
                value["dataset_id"] = edge.from_node_id
            elif edge.from_node_type == "model_entity":
                value["model_entity_id"] = edge.from_node_id

        elif is_pipeline_run_output:
            # Entity is an output from a pipeline run
            value["pipeline_run_id"] = edge.from_node_id
            if edge.to_node_type == "data_source":
                value["data_source_id"] = edge.to_node_id
            elif edge.to_node_type == "dataset":
                value["dataset_id"] = edge.to_node_id
            elif edge.to_node_type == "model_entity":
                value["model_entity_id"] = edge.to_node_id

        else:
            # Regular edges
            if edge.from_node_type == "pipeline":
                value["pipeline_id"] = edge.from_node_id
            elif edge.from_node_type == "data_source":
                value["data_source_id"] = edge.from_node_id
            elif edge.from_node_type == "dataset":
                value["dataset_id"] = edge.from_node_id
            elif edge.from_node_type == "model_entity":
                value["model_entity_id"] = edge.from_node_id
            elif edge.from_node_type == "analysis":
                value["analysis_id"] = edge.from_node_id

            if edge.to_node_type == "pipeline":
                value["pipeline_id"] = edge.to_node_id
            elif edge.to_node_type == "data_source":
                value["data_source_id"] = edge.to_node_id
            elif edge.to_node_type == "dataset":
                value["dataset_id"] = edge.to_node_id
            elif edge.to_node_type == "model_entity":
                value["model_entity_id"] = edge.to_node_id
            elif edge.to_node_type == "analysis":
                if edge.from_node_type == "analysis":
                    value["past_analysis_id"] = edge.to_node_id
                else:
                    value["analysis_id"] = edge.to_node_id

        await execute(insert(table).values([value]), commit_after=True)


async def remove_edges(edges: EdgesCreate) -> None:
    for edge in edges.edges:
        key = (edge.from_node_type, edge.to_node_type)

        # Check if this is a pipeline run edge
        is_pipeline_run_input = edge.to_node_type == "pipeline_run" and key in PIPELINE_RUN_EDGE_TABLES
        is_pipeline_run_output = edge.from_node_type == "pipeline_run" and key in PIPELINE_RUN_EDGE_TABLES

        if is_pipeline_run_input or is_pipeline_run_output:
            table, _ = PIPELINE_RUN_EDGE_TABLES[key]
        elif key in VALID_EDGES:
            table = VALID_EDGES[key]
        else:
            raise HTTPException(
                status_code=400,
                detail=f"Invalid edge: {edge.from_node_type} -> {edge.to_node_type}"
            )

        conditions = []

        # Handle pipeline run edges specially
        if is_pipeline_run_input:
            # Entity is an input to a pipeline run
            conditions.append(table.c.pipeline_run_id == edge.to_node_id)
            if edge.from_node_type == "data_source":
                conditions.append(table.c.data_source_id ==
                                  edge.from_node_id)
            elif edge.from_node_type == "dataset":
                conditions.append(table.c.dataset_id == edge.from_node_id)
            elif edge.from_node_type == "model_entity":
                conditions.append(table.c.model_entity_id ==
                                  edge.from_node_id)

        elif is_pipeline_run_output:
            # Entity is an output from a pipeline run
            conditions.append(table.c.pipeline_run_id == edge.from_node_id)
            if edge.to_node_type == "data_source":
                conditions.append(table.c.data_source_id == edge.to_node_id)
            elif edge.to_node_type == "dataset":
                conditions.append(table.c.dataset_id == edge.to_node_id)
            elif edge.to_node_type == "model_entity":
                conditions.append(table.c.model_entity_id == edge.to_node_id)

        else:
            # Regular edges
            if edge.from_node_type == "pipeline":
                conditions.append(table.c.pipeline_id == edge.from_node_id)
            elif edge.from_node_type == "data_source":
                conditions.append(table.c.data_source_id ==
                                  edge.from_node_id)
            elif edge.from_node_type == "dataset":
                conditions.append(table.c.dataset_id == edge.from_node_id)
            elif edge.from_node_type == "model_entity":
                conditions.append(table.c.model_entity_id ==
                                  edge.from_node_id)
            elif edge.from_node_type == "analysis":
                conditions.append(table.c.analysis_id == edge.from_node_id)

            if edge.to_node_type == "pipeline":
                conditions.append(table.c.pipeline_id == edge.to_node_id)
            elif edge.to_node_type == "data_source":
                conditions.append(table.c.data_source_id == edge.to_node_id)
            elif edge.to_node_type == "dataset":
                conditions.append(table.c.dataset_id == edge.to_node_id)
            elif edge.to_node_type == "model_entity":
                conditions.append(table.c.model_entity_id == edge.to_node_id)
            elif edge.to_node_type == "analysis":
                if edge.from_node_type == "analysis":
                    conditions.append(
                        table.c.past_analysis_id == edge.to_node_id)
                else:
                    conditions.append(table.c.analysis_id == edge.to_node_id)

        await execute(
            delete(table).where(and_(*conditions)),
            commit_after=True
        )


# =============================================================================
# Project Graph Building
# =============================================================================

async def get_nodes_in_graph(
    entity_type: str,
    entities: List[DataSource] | List[Dataset] | List[Pipeline] | List[ModelEntity] | List[Analysis]
) -> List[GraphNode] | List[PipelineGraphNode]:
    """
    Fetch all edges for entities and return complete GraphNode or PipelineGraphNode nodes.
    Consolidates edge fetching and node construction in a single function.
    """
    if not entities:
        return []

    entity_ids = [e.id for e in entities]

    from_entities_map = {entity_id: EdgePoints() for entity_id in entity_ids}
    to_entities_map = {entity_id: EdgePoints() for entity_id in entity_ids}

    entity_id_field = f"{entity_type}_id"
    if entity_id_field:
        for (from_type, to_type), table in VALID_EDGES.items():
            if from_type == entity_type:
                from_field = f"{from_type}_id"
                to_field = f"{to_type}_id"
                if to_type == "analysis" and from_type == "analysis":
                    to_field = "past_analysis_id"

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
                    elif to_type == "model_entity":
                        to_entities.model_entities.append(target_id)
                    elif to_type == "analysis":
                        to_entities.analyses.append(target_id)

            elif to_type == entity_type:
                from_field = f"{from_type}_id"
                to_field = f"{to_type}_id"
                if to_type == "analysis" and from_type == "analysis":
                    to_field = "past_analysis_id"

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
                    elif from_type == "model_entity":
                        from_entities.model_entities.append(source_id)
                    elif from_type == "analysis":
                        from_entities.analyses.append(source_id)

        # Check pipeline run edges - entities can be inputs to or outputs from runs
        for (from_type, to_type), (table, direction) in PIPELINE_RUN_EDGE_TABLES.items():
            if direction == "input" and from_type == entity_type:
                # This entity type is an input to pipeline runs
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
                # This entity type is an output from pipeline runs
                entity_field = f"{entity_type}_id"
                records = await fetch_all(
                    select(table).where(
                        getattr(table.c, entity_field).in_(entity_ids))
                )

                for record in records:
                    entity_id = record[entity_field]
                    run_id = record["pipeline_run_id"]
                    from_entities_map[entity_id].pipeline_runs.append(run_id)

    nodes = []
    if entity_type == "pipeline":
        for entity in entities:
            run_nodes = await _get_pipeline_run_nodes_in_graph(entity.runs)
            nodes.append(PipelineGraphNode(
                id=entity.id,
                name=entity.name,
                description=entity.description,
                from_entities=from_entities_map[entity.id],
                to_entities=to_entities_map[entity.id],
                runs=run_nodes
            ))
    else:
        for entity in entities:
            nodes.append(GraphNode(
                id=entity.id,
                name=entity.name,
                description=entity.description,
                from_entities=from_entities_map[entity.id],
                to_entities=to_entities_map[entity.id]
            ))

    return nodes


async def build_entity_graph(
        data_sources: List[DataSource],
        datasets: List[Dataset],
        pipelines: List[Pipeline],
        model_entities: List[ModelEntity],
        analyses: List[Analysis],
        exclude_ids: bool = False
) -> EntityGraph | EntityGraphUsingNames:
    # Build complete nodes with edges for each entity type
    data_sources_in_graph = await get_nodes_in_graph("data_source", data_sources)
    datasets_in_graph = await get_nodes_in_graph("dataset", datasets)
    pipelines_in_graph = await get_nodes_in_graph("pipeline", pipelines)
    model_entities_in_graph = await get_nodes_in_graph("model_entity", model_entities)
    analyses_in_graph = await get_nodes_in_graph("analysis", analyses)

    output_model = EntityGraphUsingNames if exclude_ids else EntityGraph

    # Collect all pipeline runs from all pipelines for top-level access
    all_pipeline_runs = []
    for pipeline_node in pipelines_in_graph:
        if hasattr(pipeline_node, 'runs'):
            all_pipeline_runs.extend(pipeline_node.runs)

    if exclude_ids:
        return output_model(
            data_sources=data_sources_in_graph,
            datasets=datasets_in_graph,
            pipelines=pipelines_in_graph,
            analyses=analyses_in_graph,
            model_entities=model_entities_in_graph,
            pipeline_runs=all_pipeline_runs
        )
    else:
        return output_model(
            data_sources=data_sources_in_graph,
            datasets=datasets_in_graph,
            pipelines=pipelines_in_graph,
            analyses=analyses_in_graph,
            model_entities=model_entities_in_graph
        )


async def get_entity_details(user_id: uuid.UUID, entity_ids: List[uuid.UUID], recursive: bool = True) -> EntityDetailsResponse:
    """
    Get detailed descriptions of entities including their inputs and outputs.
    If recursive is True, fetches details for all input entities recursively.
    """
    EntityMap = dict[tuple[uuid.UUID, str], DataSource |
                     Dataset | Pipeline | ModelEntity | Analysis]

    all_entity_ids: set[uuid.UUID] = set(entity_ids)

    if recursive:
        # Recursively discover all input entity IDs
        ids_to_process: List[uuid.UUID] = list(entity_ids)
        processed_ids: set[uuid.UUID] = set()

        while ids_to_process:
            current_id: uuid.UUID = ids_to_process.pop()
            if current_id in processed_ids:
                continue
            processed_ids.add(current_id)

            for (from_type, to_type), table in VALID_EDGES.items():
                to_field: str = f"{to_type}_id"
                if to_type == "analysis" and from_type == "analysis":
                    to_field = "past_analysis_id"

                from_field: str = f"{from_type}_id"

                records = await fetch_all(
                    select(table).where(
                        getattr(table.c, to_field) == current_id)
                )

                for record in records:
                    input_id: uuid.UUID = record[from_field]
                    if input_id not in all_entity_ids:
                        all_entity_ids.add(input_id)
                        ids_to_process.append(input_id)

    all_entity_ids_list: List[uuid.UUID] = list(all_entity_ids)
    data_sources = await get_user_data_sources(user_id, all_entity_ids_list)
    datasets = await get_user_datasets(user_id, all_entity_ids_list)
    pipelines = await get_user_pipelines(user_id, all_entity_ids_list)
    model_entities = await get_user_model_entities(user_id, all_entity_ids_list)
    analyses = await get_user_analyses(user_id, all_entity_ids_list)

    entity_map: EntityMap = {}

    for ds in data_sources:
        entity_map[(ds.id, "data_source")] = ds
    for dataset in datasets:
        entity_map[(dataset.id, "dataset")] = dataset
    for pipeline in pipelines:
        entity_map[(pipeline.id, "pipeline")] = pipeline
    for me in model_entities:
        entity_map[(me.id, "model_entity")] = me
    for analysis in analyses:
        entity_map[(analysis.id, "analysis")] = analysis

    # Fetch edges for all entities
    from_entities_edges_map: dict[tuple[uuid.UUID, str], EdgePoints] = {}
    to_entities_edges_map: dict[tuple[uuid.UUID, str], EdgePoints] = {}
    for entity_key in entity_map.keys():
        entity_id: uuid.UUID
        entity_type: str
        entity_id, entity_type = entity_key
        from_entities = EdgePoints()
        to_entities = EdgePoints()

        for (from_type, to_type), table in VALID_EDGES.items():
            if from_type == entity_type:
                from_field: str = f"{from_type}_id"
                to_field: str = f"{to_type}_id"
                if to_type == "analysis" and from_type == "analysis":
                    to_field = "past_analysis_id"

                records = await fetch_all(
                    select(table).where(
                        getattr(table.c, from_field) == entity_id)
                )

                for record in records:
                    target_id: uuid.UUID = record[to_field]
                    if to_type == "data_source":
                        to_entities.data_sources.append(target_id)
                    elif to_type == "dataset":
                        to_entities.datasets.append(target_id)
                    elif to_type == "pipeline":
                        to_entities.pipelines.append(target_id)
                    elif to_type == "model_entity":
                        to_entities.model_entities.append(target_id)
                    elif to_type == "analysis":
                        to_entities.analyses.append(target_id)

        for (from_type, to_type), table in VALID_EDGES.items():
            if to_type == entity_type:
                from_field: str = f"{from_type}_id"
                to_field: str = f"{to_type}_id"
                if to_type == "analysis" and from_type == "analysis":
                    to_field = "past_analysis_id"

                records = await fetch_all(
                    select(table).where(
                        getattr(table.c, to_field) == entity_id)
                )

                for record in records:
                    source_id: uuid.UUID = record[from_field]
                    if from_type == "data_source":
                        from_entities.data_sources.append(source_id)
                    elif from_type == "dataset":
                        from_entities.datasets.append(source_id)
                    elif from_type == "pipeline":
                        from_entities.pipelines.append(source_id)
                    elif from_type == "model_entity":
                        from_entities.model_entities.append(source_id)
                    elif from_type == "analysis":
                        from_entities.analyses.append(source_id)

        # Check pipeline run edges - entities can be inputs to or outputs from runs
        for (from_type, to_type), (table, direction) in PIPELINE_RUN_EDGE_TABLES.items():
            if direction == "input" and from_type == entity_type:
                # This entity type is an input to pipeline runs
                entity_field: str = f"{entity_type}_id"
                records = await fetch_all(
                    select(table).where(
                        getattr(table.c, entity_field) == entity_id)
                )

                for record in records:
                    run_id: uuid.UUID = record["pipeline_run_id"]
                    to_entities.pipeline_runs.append(run_id)

            elif direction == "output" and to_type == entity_type:
                # This entity type is an output from pipeline runs
                entity_field: str = f"{entity_type}_id"
                records = await fetch_all(
                    select(table).where(
                        getattr(table.c, entity_field) == entity_id)
                )

                for record in records:
                    run_id: uuid.UUID = record["pipeline_run_id"]
                    from_entities.pipeline_runs.append(run_id)

        from_entities_edges_map[entity_key] = from_entities
        to_entities_edges_map[entity_key] = to_entities

    # Generate descriptions for all entities (no duplicates due to entity_map keys being unique)
    result_details: List[EntityDetail] = []

    for entity_key, entity in entity_map.items():
        entity_id, entity_type = entity_key
        entity: DataSource | Dataset | Pipeline | ModelEntity | Analysis
        from_entities = from_entities_edges_map[entity_key]
        to_entities = to_entities_edges_map[entity_key]

        description: str
        if entity_type == "data_source":
            description = get_data_source_description(
                entity, from_entities, to_entities, entity_map)
        elif entity_type == "dataset":
            description = get_dataset_description(
                entity, from_entities, to_entities, entity_map)
        elif entity_type == "pipeline":
            description = get_pipeline_description(
                entity, from_entities, to_entities, entity_map)
        elif entity_type == "model_entity":
            description = get_model_entity_description(
                entity, from_entities, to_entities, entity_map)
        elif entity_type == "analysis":
            description = get_analysis_description(
                entity, from_entities, to_entities, entity_map)
        else:
            raise HTTPException(
                status_code=400,
                detail=f"Invalid entity type: {entity_type}"
            )

        result_details.append(EntityDetail(
            entity_id=entity_id,
            entity_type=entity_type,
            name=entity.name,
            description=description,
            inputs=from_entities,
            outputs=to_entities
        ))

    return EntityDetailsResponse(entity_details=result_details)


###


async def _get_pipeline_run_nodes_in_graph(pipeline_runs: List[PipelineRunInDB]) -> List[GraphNode]:
    """
    Build GraphNode objects for pipeline runs with their input/output edges.
    """
    if not pipeline_runs:
        return []

    run_ids = [run.id for run in pipeline_runs]
    from_entities_map = {run_id: EdgePoints() for run_id in run_ids}
    to_entities_map = {run_id: EdgePoints() for run_id in run_ids}

    # Fetch input edges for runs
    for (from_type, to_type), (table, direction) in PIPELINE_RUN_EDGE_TABLES.items():
        if direction == "input" and to_type == "pipeline_run":
            # Inputs to pipeline runs
            records = await fetch_all(
                select(table).where(table.c.pipeline_run_id.in_(run_ids))
            )

            for record in records:
                run_id = record["pipeline_run_id"]
                from_entities = from_entities_map[run_id]

                if from_type == "data_source":
                    from_entities.data_sources.append(record["data_source_id"])
                elif from_type == "dataset":
                    from_entities.datasets.append(record["dataset_id"])
                elif from_type == "model_entity":
                    from_entities.model_entities.append(
                        record["model_entity_id"])

        elif direction == "output" and from_type == "pipeline_run":
            # Outputs from pipeline runs
            records = await fetch_all(
                select(table).where(table.c.pipeline_run_id.in_(run_ids))
            )

            for record in records:
                run_id = record["pipeline_run_id"]
                to_entities = to_entities_map[run_id]

                if to_type == "data_source":
                    to_entities.data_sources.append(record["data_source_id"])
                elif to_type == "dataset":
                    to_entities.datasets.append(record["dataset_id"])
                elif to_type == "model_entity":
                    to_entities.model_entities.append(
                        record["model_entity_id"])

    # Build GraphNode objects for runs
    run_nodes = []
    for run in pipeline_runs:
        run_nodes.append(GraphNode(
            id=run.id,
            name=run.name,
            description=run.description or "",
            from_entities=from_entities_map[run.id],
            to_entities=to_entities_map[run.id]
        ))

    return run_nodes
