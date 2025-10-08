import uuid
from datetime import datetime, timezone
from typing import List, Optional, Literal
from sqlalchemy import select, insert, or_, and_

from synesis_api.database.service import fetch_all, execute, fetch_one
from synesis_api.modules.pipeline.models import (
    pipeline,
    function_in_pipeline,
    pipeline_periodic_schedule,
    pipeline_on_event_schedule,
    model_entity_in_pipeline,
    pipeline_output_object_group_definition,
    object_group_in_pipeline,
    pipeline_graph_node,
    pipeline_graph_edge,
    pipeline_graph_dataset_node,
    pipeline_graph_function_node,
    pipeline_graph_model_entity_node,
    pipeline_run,
    pipeline_output_dataset,
    pipeline_output_model_entity
)
from synesis_api.modules.function.service import get_functions
from synesis_schemas.main_server import (
    PipelineInDB,
    FunctionInPipelineInDB,
    PipelineFull,
    PipelinePeriodicScheduleInDB,
    PipelineCreate,
    PipelineSources,
    ModelEntityInPipelineInDB,
    ObjectGroupInPipelineInDB,
    PipelineOutputObjectGroupDefinitionInDB,
    PipelineGraphNodeInDB,
    PipelineGraphDatasetNodeInDB,
    PipelineGraphFunctionNodeInDB,
    PipelineGraphModelEntityNodeInDB,
    PipelineGraphEdgeInDB,
    PipelineGraphNode,
    PipelineGraph,
    PipelineRunInDB,
    PipelineOutputDatasetInDB,
    PipelineOutputModelEntityInDB,
    PipelineRunDatasetOutputCreate,
    PipelineRunModelEntityOutputCreate
)
from synesis_api.modules.project.service import get_pipeline_ids_in_project
from synesis_api.modules.data_objects.service import get_object_groups


async def create_pipeline(
    user_id: uuid.UUID,
    pipeline_create: PipelineCreate,
) -> PipelineInDB:

    pipeline_obj = PipelineInDB(
        id=uuid.uuid4(),
        user_id=user_id,
        **pipeline_create.model_dump(),
        created_at=datetime.now(timezone.utc),
        updated_at=datetime.now(timezone.utc)
    )

    await execute(insert(pipeline).values(**pipeline_obj.model_dump()), commit_after=True)

    if len(pipeline_create.periodic_schedules) > 0:

        periodic_schedule_records = [
            PipelinePeriodicScheduleInDB(
                id=uuid.uuid4(),
                pipeline_id=pipeline_obj.id,
                start_time=periodic_schedule.start_time if periodic_schedule.start_time else datetime.now(
                    timezone.utc),
                **periodic_schedule.model_dump(),
                created_at=datetime.now(timezone.utc),
                updated_at=datetime.now(timezone.utc)
            ).model_dump() for periodic_schedule in pipeline_create.periodic_schedules
        ]

        await execute(insert(pipeline_periodic_schedule).values(periodic_schedule_records), commit_after=True)

    # TODO: Add on-event schedules

    fn_in_pipeline_records = [
        FunctionInPipelineInDB(
            id=uuid.uuid4(),
            pipeline_id=pipeline_obj.id,
            function_id=function_id,
            created_at=datetime.now(timezone.utc),
            updated_at=datetime.now(timezone.utc)
        ) for function_id in pipeline_create.function_ids
    ]

    pipeline_input_object_group_from_dataset_records = []
    for group in pipeline_create.input_object_groups:
        pipeline_input_object_group_from_dataset_obj = ObjectGroupInPipelineInDB(
            id=uuid.uuid4(),
            pipeline_id=pipeline_obj.id,
            **group.model_dump(),
            created_at=datetime.now(timezone.utc),
            updated_at=datetime.now(timezone.utc)
        )
        pipeline_input_object_group_from_dataset_records.append(
            pipeline_input_object_group_from_dataset_obj.model_dump())

    output_object_group_definition_records = []
    for group in pipeline_create.output_object_group_definitions:
        pipeline_object_group_output_definition_obj = PipelineOutputObjectGroupDefinitionInDB(
            id=uuid.uuid4(),
            pipeline_id=pipeline_obj.id,
            **group.model_dump(),
            created_at=datetime.now(timezone.utc),
            updated_at=datetime.now(timezone.utc)
        )
        output_object_group_definition_records.append(
            pipeline_object_group_output_definition_obj.model_dump())

    if len(fn_in_pipeline_records) > 0:
        await execute(insert(function_in_pipeline).values(fn_in_pipeline_records), commit_after=True)
    if len(pipeline_input_object_group_from_dataset_records) > 0:
        await execute(insert(object_group_in_pipeline).values(pipeline_input_object_group_from_dataset_records), commit_after=True)
    if len(output_object_group_definition_records) > 0:
        await execute(insert(pipeline_output_object_group_definition).values(output_object_group_definition_records), commit_after=True)

    model_entity_in_pipeline_records = [ModelEntityInPipelineInDB(
        pipeline_id=pipeline_obj.id,
        **model_entity.model_dump(),
        created_at=datetime.now(timezone.utc),
        updated_at=datetime.now(timezone.utc)
    ).model_dump() for model_entity in pipeline_create.input_model_entities]

    if len(model_entity_in_pipeline_records) > 0:
        await execute(insert(model_entity_in_pipeline).values(model_entity_in_pipeline_records), commit_after=True)

    # pipeline_node_records: List[PipelineGraphNodeInDB] = []
    # pipeline_edge_records: List[PipelineGraphEdgeInDB] = []
    # pipeline_dataset_node_records: List[PipelineGraphDatasetNodeInDB] = []
    # pipeline_function_node_records: List[PipelineGraphFunctionNodeInDB] = []
    # pipeline_model_entity_node_records: List[PipelineGraphModelEntityNodeInDB] = []

    # for node in pipeline_create.computational_graph.nodes:
    #     node_record = PipelineGraphNodeInDB(
    #         id=uuid.uuid4(),
    #         type=node.type,
    #         pipeline_id=pipeline_obj.id,
    #         created_at=datetime.now(timezone.utc),
    #         updated_at=datetime.now(timezone.utc)
    #     )
    #     pipeline_node_records.append(node_record.model_dump())

    #     if node.type == "dataset":
    #         pipeline_dataset_node_records.append(PipelineGraphDatasetNodeInDB(
    #             id=node_record.id,
    #             dataset_id=node.entity_id,
    #             created_at=datetime.now(timezone.utc),
    #             updated_at=datetime.now(timezone.utc)
    #         ).model_dump())

    #     elif node.type == "function":
    #         pipeline_function_node_records.append(PipelineGraphFunctionNodeInDB(
    #             id=node_record.id,
    #             function_id=node.entity_id,
    #             created_at=datetime.now(timezone.utc),
    #             updated_at=datetime.now(timezone.utc)
    #         ).model_dump())

    #     elif node.type == "model_entity":
    #         pipeline_model_entity_node_records.append(PipelineGraphModelEntityNodeInDB(
    #             id=node_record.id,
    #             model_entity_id=node.entity_id,
    #             function_type=node.model_function_type,
    #             created_at=datetime.now(timezone.utc),
    #             updated_at=datetime.now(timezone.utc)
    #         ).model_dump())

    # for node_record in pipeline_node_records:

    #     dset_node = next(n for n in pipeline_dataset_node_records if n.id == node_record.id)
    #     fn_node = next(n for n in pipeline_function_node_records if n.id == node_record.id)
    #     me_node = next(n for n in pipeline_model_entity_node_records if n.id == node_record.id)

    #     from_dset_ids = [n.id for n in]

    #     for from_model_entity_id in node.from_model_entity_ids:
    #         pipeline_edge_records.append(PipelineGraphEdgeInDB(
    #             from_node_id=node_record.id,
    #             to_node_id=from_model_entity_id,
    #             created_at=datetime.now(timezone.utc),
    #             updated_at=datetime.now(timezone.utc)
    #         ).model_dump())

    #     for from_function_id in node.from_function_ids:
    #         pipeline_edge_records.append(PipelineGraphEdgeInDB(
    #             from_node_id=node_record.id,
    #             to_node_id=from_function_id,
    #             created_at=datetime.now(timezone.utc),
    #             updated_at=datetime.now(timezone.utc)
    #         ).model_dump())

    #     for from_dataset_id in node.from_dataset_ids:
    #         pipeline_edge_records.append(PipelineGraphEdgeInDB(
    #             from_node_id=node_record.id,
    #             to_node_id=from_dataset_id,
    #             created_at=datetime.now(timezone.utc),
    #             updated_at=datetime.now(timezone.utc)
    #         ).model_dump())

    # if len(pipeline_node_records) > 0:
    #     await execute(insert(pipeline_graph_node).values(pipeline_node_records), commit_after=True)
    # if len(pipeline_edge_records) > 0:
    #     await execute(insert(pipeline_graph_edge).values(pipeline_edge_records), commit_after=True)
    # if len(pipeline_dataset_node_records) > 0:
    #     await execute(insert(pipeline_graph_dataset_node).values(pipeline_dataset_node_records), commit_after=True)
    # if len(pipeline_function_node_records) > 0:
    #     await execute(insert(pipeline_graph_function_node).values(pipeline_function_node_records), commit_after=True)
    # if len(pipeline_model_entity_node_records) > 0:
    #     await execute(insert(pipeline_graph_model_entity_node).values(pipeline_model_entity_node_records), commit_after=True)

    return pipeline_obj


async def get_user_pipelines(
    user_id: uuid.UUID,
    pipeline_ids: Optional[List[uuid.UUID]] = None,
    project_id: Optional[uuid.UUID] = None
) -> List[PipelineFull]:

    # pipelines bare
    pipeline_query = select(pipeline).where(pipeline.c.user_id == user_id)

    if pipeline_ids:
        pipeline_query = pipeline_query.where(pipeline.c.id.in_(pipeline_ids))
    if project_id:
        pipeline_ids = await get_pipeline_ids_in_project(project_id)
        pipeline_query = pipeline_query.where(pipeline.c.id.in_(pipeline_ids))

    pipelines = await fetch_all(pipeline_query)
    pipeline_ids = [p["id"] for p in pipelines]

    # pipeline runs
    pipeline_runs_query = select(pipeline_run).where(
        pipeline_run.c.pipeline_id.in_(pipeline_ids))
    pipeline_runs = await fetch_all(pipeline_runs_query)

    # functions in the pipelines
    functions_in_pipelines_query = select(function_in_pipeline).where(
        function_in_pipeline.c.pipeline_id.in_(pipeline_ids))
    functions_in_pipelines = await fetch_all(functions_in_pipelines_query)

    function_records = await get_functions(
        [f["function_id"] for f in functions_in_pipelines])

    # schedules
    periodic_schedules_query = select(pipeline_periodic_schedule).where(
        pipeline_periodic_schedule.c.pipeline_id.in_(pipeline_ids))
    on_event_schedules_query = select(pipeline_on_event_schedule).where(
        pipeline_on_event_schedule.c.pipeline_id.in_(pipeline_ids))

    periodic_schedules = await fetch_all(periodic_schedules_query)
    on_event_schedules = await fetch_all(on_event_schedules_query)

    # inputs / outputs
    model_entities_query = select(model_entity_in_pipeline).where(
        model_entity_in_pipeline.c.pipeline_id.in_(pipeline_ids))

    model_entities = await fetch_all(model_entities_query)

    input_object_group_from_dataset_query = select(object_group_in_pipeline).where(
        object_group_in_pipeline.c.pipeline_id.in_(pipeline_ids))
    output_object_group_definition_query = select(pipeline_output_object_group_definition).where(
        pipeline_output_object_group_definition.c.pipeline_id.in_(pipeline_ids))

    input_object_groups = await fetch_all(input_object_group_from_dataset_query)
    output_object_group_definitions = await fetch_all(output_object_group_definition_query)

    # computational graph
    pipeline_nodes_query = select(pipeline_graph_node, pipeline_graph_dataset_node, pipeline_graph_function_node, pipeline_graph_model_entity_node).join(
        pipeline_graph_dataset_node, pipeline_graph_node.c.id == pipeline_graph_dataset_node.c.id
    ).join(
        pipeline_graph_function_node, pipeline_graph_node.c.id == pipeline_graph_function_node.c.id
    ).join(
        pipeline_graph_model_entity_node, pipeline_graph_node.c.id == pipeline_graph_model_entity_node.c.id
    ).where(
        pipeline_graph_node.c.pipeline_id.in_(pipeline_ids)
    )

    pipeline_nodes = await fetch_all(pipeline_nodes_query)

    pipeline_edges_query = select(pipeline_graph_edge).where(
        or_(pipeline_graph_edge.c.from_node_id.in_([n["id"] for n in pipeline_nodes]),
            pipeline_graph_edge.c.to_node_id.in_([n["id"] for n in pipeline_nodes]))
    )

    pipeline_edges = await fetch_all(pipeline_edges_query)

    output_objs = []
    for pipe_id in pipeline_ids:
        pipe_record = next(p for p in pipelines if p["id"] == pipe_id)
        runs_records = [
            r for r in pipeline_runs if r["pipeline_id"] == pipe_id]
        periodic_schedules_records = [
            s for s in periodic_schedules if s["pipeline_id"] == pipe_id]
        on_event_schedules_records = [
            s for s in on_event_schedules if s["pipeline_id"] == pipe_id]
        model_entity_records = [
            s for s in model_entities if s["pipeline_id"] == pipe_id]
        output_object_group_definition_records = [
            s for s in output_object_group_definitions if s["pipeline_id"] == pipe_id]

        input_object_group_objs = await get_object_groups(
            group_ids=[s["object_group_id"]
                       for s in input_object_groups if s["pipeline_id"] == pipe_id],
            include_objects=False
        )

        function_ids_in_pipeline = [
            f["function_id"] for f in functions_in_pipelines if f["pipeline_id"] == pipe_id]
        functions_records = [
            f for f in function_records if f.id in function_ids_in_pipeline]

        nodes_in_pipeline = [
            n for n in pipeline_nodes if n["pipeline_id"] == pipe_id]
        edges_in_pipeline = [e for e in pipeline_edges if e["from_node_id"] in [
            n["id"] for n in nodes_in_pipeline] or e["to_node_id"] in [n["id"] for n in nodes_in_pipeline]]

        nodes_in_pipeline_objs: List[PipelineGraphNode] = []
        for node in nodes_in_pipeline:
            if node["type"] == "dataset":
                nodes_in_pipeline_objs.append(PipelineGraphNode(
                    id=node["id"],
                    entity_id=node["dataset_id"],
                    type="dataset",
                    model_function_type=node["function_type"],
                    from_dataset_ids=[
                        e["from_node_id"] for e in edges_in_pipeline if e["to_node_id"] == node["id"]],
                    from_function_ids=[
                        e["from_node_id"] for e in edges_in_pipeline if e["to_node_id"] == node["id"]],
                    from_model_entity_ids=[
                        e["from_node_id"] for e in edges_in_pipeline if e["to_node_id"] == node["id"]]
                ))

        output_objs.append(PipelineFull(
            **pipe_record,
            functions=functions_records,
            runs=runs_records,
            periodic_schedules=periodic_schedules_records,
            on_event_schedules=on_event_schedules_records,
            model_entities=model_entity_records,
            input_object_groups=input_object_group_objs,
            output_object_group_definitions=output_object_group_definition_records,
            computational_graph=PipelineGraph(nodes=nodes_in_pipeline_objs),
            sources=PipelineSources(
                dataset_ids=list(
                    set(o.dataset_id for o in input_object_group_objs)),
                model_entity_ids=list(
                    set(o["model_entity_id"] for o in model_entity_records)),
            )
        ))
    return output_objs


async def get_user_pipelines_by_ids(user_id: uuid.UUID, pipeline_ids: List[uuid.UUID]) -> List[PipelineFull]:
    return await get_user_pipelines(user_id, pipeline_ids=pipeline_ids)


async def get_project_pipelines(user_id: uuid.UUID, project_id: uuid.UUID) -> List[PipelineFull]:
    return await get_user_pipelines(user_id, project_id=project_id)


async def create_pipeline_run(pipeline_id: uuid.UUID) -> PipelineRunInDB:
    pipeline_run_obj = PipelineRunInDB(
        id=uuid.uuid4(),
        pipeline_id=pipeline_id,
        status="running",
        start_time=datetime.now(timezone.utc),
        created_at=datetime.now(timezone.utc),
        updated_at=datetime.now(timezone.utc))
    await execute(insert(pipeline_run).values(pipeline_run_obj.model_dump()), commit_after=True)
    return pipeline_run_obj


async def get_pipeline_runs(
    user_id: uuid.UUID,
    only_running: bool = False,
    pipeline_ids: Optional[List[uuid.UUID]] = None,
    run_ids: Optional[List[uuid.UUID]] = None
) -> List[PipelineRunInDB]:

    pipeline_runs_query = select(pipeline_run
                                 ).join(pipeline, pipeline_run.c.pipeline_id == pipeline.c.id
                                        ).where(pipeline.c.user_id == user_id)

    if pipeline_ids is not None:
        pipeline_runs_query = pipeline_runs_query.where(
            pipeline_run.c.pipeline_id.in_(pipeline_ids))
    if run_ids is not None:
        pipeline_runs_query = pipeline_runs_query.where(
            pipeline_run.c.id.in_(run_ids))
    if only_running:
        pipeline_runs_query = pipeline_runs_query.where(
            pipeline_run.c.status == "running")

    pipeline_runs = await fetch_all(pipeline_runs_query)

    return [PipelineRunInDB(**run) for run in pipeline_runs]


async def update_pipeline_run_status(pipeline_run_id: uuid.UUID, status: Literal["running", "completed", "failed"]) -> PipelineRunInDB:
    pipeline_run_obj = await fetch_one(select(pipeline_run).where(pipeline_run.c.id == pipeline_run_id))
    await execute(pipeline_run.update().where(pipeline_run.c.id == pipeline_run_id).values(status=status), commit_after=True)
    pipeline_run_obj["status"] = status
    return PipelineRunInDB(**pipeline_run_obj)


async def create_pipeline_output_dataset(pipeline_id: uuid.UUID, request: PipelineRunDatasetOutputCreate) -> PipelineOutputDatasetInDB:
    pipeline_output_dataset_obj = PipelineOutputDatasetInDB(
        pipeline_id=pipeline_id,
        dataset_id=request.dataset_id,
        created_at=datetime.now(timezone.utc),
        updated_at=datetime.now(timezone.utc))
    await execute(insert(pipeline_output_dataset).values(pipeline_output_dataset_obj.model_dump()), commit_after=True)
    return pipeline_output_dataset_obj


async def create_pipeline_output_model_entity(pipeline_id: uuid.UUID, request: PipelineRunModelEntityOutputCreate) -> PipelineOutputModelEntityInDB:
    pipeline_output_model_entity_obj = PipelineOutputModelEntityInDB(
        pipeline_id=pipeline_id,
        model_entity_id=request.model_entity_id,
        created_at=datetime.now(timezone.utc),
        updated_at=datetime.now(timezone.utc))
    await execute(insert(pipeline_output_model_entity).values(pipeline_output_model_entity_obj.model_dump()), commit_after=True)
    return pipeline_output_model_entity_obj
