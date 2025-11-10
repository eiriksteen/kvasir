import uuid
from typing import Literal, Optional, List, Union
from datetime import datetime, timezone
from sqlalchemy import select, insert
from pydantic_ai.messages import ModelMessagesTypeAdapter, ModelMessage

from synesis_api.client import MainServerClient, post_run_swe, post_run_analysis
from synesis_api.database.service import fetch_all, execute, fetch_one
from synesis_api.modules.analysis.service import create_analysis
from synesis_api.modules.pipeline.service import create_pipeline
from synesis_api.modules.project.service import add_entity_to_project
from synesis_schemas.main_server import (
    RunInDB,
    DataSourceInRunInDB,
    RunCreate,
    DatasetInRunInDB,
    ModelEntityInRunInDB,
    PipelineInRunInDB,
    AnalysisFromRunInDB,
    PipelineFromRunInDB,
    PipelineCreate,
    AddEntityToProject,
    AnalysisCreate,
    AnalysisInRunInDB,
    EdgesCreate,
    EdgeDefinition,
    Run,
    RunEntityIds,
    RunStatusUpdate,
    RunMessageCreate,
    RunMessageCreatePydantic,
    RunMessageInDB,
    RunPydanticMessageInDB,
)
from synesis_schemas.project_server import RunAnalysisRequest, RunSWERequest
from synesis_api.modules.entity_graph.service import create_edges
from synesis_api.modules.runs.models import (
    run,
    run_pydantic_message,
    run_message,
    data_source_in_run,
    dataset_in_run,
    model_entity_in_run,
    pipeline_in_run,
    pipeline_from_run,
    analysis_from_run,
    analysis_in_run,
    data_source_from_run,
    dataset_from_run,
    model_entity_from_run,
)


async def create_run(user_id: uuid.UUID, run_create: RunCreate) -> RunInDB:

    run_record = RunInDB(
        id=uuid.uuid4(),
        user_id=user_id,
        **run_create.model_dump(),
        started_at=datetime.now(timezone.utc),
        status=run_create.initial_status
    )

    data_sources_in_run_records = []
    datasets_in_run_records = []
    model_entities_in_run_records = []
    pipelines_in_run_records = []
    analysis_in_run_records = []

    for data_source_id in run_create.data_sources_in_run:
        data_sources_in_run_records.append(DataSourceInRunInDB(
            run_id=run_record.id,
            data_source_id=data_source_id,
            created_at=datetime.now(timezone.utc)
        ).model_dump())
    for dataset_id in run_create.datasets_in_run:
        datasets_in_run_records.append(DatasetInRunInDB(
            run_id=run_record.id,
            dataset_id=dataset_id,
            created_at=datetime.now(timezone.utc)
        ).model_dump())
    for model_entity_id in run_create.model_entities_in_run:
        model_entities_in_run_records.append(ModelEntityInRunInDB(
            run_id=run_record.id,
            model_entity_id=model_entity_id,
            created_at=datetime.now(timezone.utc)
        ).model_dump())
    for pipeline_id in run_create.pipelines_in_run:
        pipelines_in_run_records.append(PipelineInRunInDB(
            run_id=run_record.id,
            pipeline_id=pipeline_id,
            created_at=datetime.now(timezone.utc)
        ).model_dump())
    for analysis_id in run_create.analyses_in_run:
        analysis_in_run_records.append(AnalysisInRunInDB(
            run_id=run_record.id,
            analysis_id=analysis_id,
            created_at=datetime.now(timezone.utc)
        ).model_dump())

    # Create the entity_from_run record from the associated entity id
    analysis_from_run_record = None
    pipeline_from_run_record = None
    if run_record.type == "analysis" and run_create.target_entity_id:
        analysis_from_run_record = AnalysisFromRunInDB(
            run_id=run_record.id,
            analysis_id=run_create.target_entity_id,
            created_at=datetime.now(timezone.utc)
        )
    elif run_record.type == "swe" and run_create.target_entity_id:
        pipeline_from_run_record = PipelineFromRunInDB(
            run_id=run_record.id,
            pipeline_id=run_create.target_entity_id,
            created_at=datetime.now(timezone.utc)
        )

    await execute(run.insert().values(run_record.model_dump()), commit_after=True)

    if data_sources_in_run_records:
        await execute(insert(data_source_in_run).values(data_sources_in_run_records), commit_after=True)
    if datasets_in_run_records:
        await execute(insert(dataset_in_run).values(datasets_in_run_records), commit_after=True)
    if model_entities_in_run_records:
        await execute(insert(model_entity_in_run).values(model_entities_in_run_records), commit_after=True)
    if analysis_in_run_records:
        await execute(insert(analysis_in_run).values(analysis_in_run_records), commit_after=True)
    if pipelines_in_run_records:
        await execute(insert(pipeline_in_run).values(pipelines_in_run_records), commit_after=True)

    if analysis_from_run_record:
        await execute(insert(analysis_from_run).values(analysis_from_run_record.model_dump()), commit_after=True)
    if pipeline_from_run_record:
        await execute(insert(pipeline_from_run).values(pipeline_from_run_record.model_dump()), commit_after=True)

    return run_record


async def launch_run(user_id: uuid.UUID, client: MainServerClient, run_id: uuid.UUID):
    run_record = RunInDB(**(await fetch_one(select(run).where(run.c.id == run_id))))
    run_record.status = "running"
    data_source_ids = [rec["data_source_id"] for rec in await fetch_all(
        select(data_source_in_run).where(
            data_source_in_run.c.run_id == run_id))]
    dataset_ids = [rec["dataset_id"] for rec in await fetch_all(
        select(dataset_in_run).where(
            dataset_in_run.c.run_id == run_id))]
    model_entity_ids = [rec["model_entity_id"] for rec in await fetch_all(
        select(model_entity_in_run).where(
            model_entity_in_run.c.run_id == run_id))]
    analysis_ids = [rec["analysis_id"] for rec in await fetch_all(
        select(analysis_in_run).where(
            analysis_in_run.c.run_id == run_id))]
    # pipeline_ids = [rec["pipeline_id"] for rec in await fetch_all(
    #     select(pipeline_in_run).where(
    #         pipeline_in_run.c.run_id == run_id))]

    analysis_from_run_record = await fetch_one(
        select(analysis_from_run).where(
            analysis_from_run.c.run_id == run_id))
    pipeline_from_run_record = await fetch_one(
        select(pipeline_from_run).where(
            pipeline_from_run.c.run_id == run_id))

    if analysis_from_run_record:
        target_entity_id = analysis_from_run_record["analysis_id"]
    elif pipeline_from_run_record:
        target_entity_id = pipeline_from_run_record["pipeline_id"]
    else:
        target_entity_id = None
    # else:
    #     raise RuntimeError(
    #         "No associated entity found for run (the analysis or pipeline entity must be created before the run is launched. The orchestrator should do this automatically. )")

    if run_record.type == "swe":
        if target_entity_id is None:
            pipeline_create = PipelineCreate(
                name=run_record.run_name,
                description=run_record.plan_and_deliverable_description_for_agent,
                # input_data_source_ids=data_source_ids,
                # input_dataset_ids=dataset_ids,
                # input_model_entity_ids=model_entity_ids,
                # input_analysis_ids=analysis_ids
            )
            target_entity_id = (await create_pipeline(pipeline_create=pipeline_create, user_id=user_id)).id
            await add_entity_to_project(user_id, AddEntityToProject(
                project_id=run_record.project_id,
                entity_type="pipeline",
                entity_id=target_entity_id
            ))
            pipeline_from_run_record = PipelineFromRunInDB(
                run_id=run_id,
                pipeline_id=target_entity_id,
                created_at=datetime.now(timezone.utc)
            )
            await execute(insert(pipeline_from_run).values(pipeline_from_run_record.model_dump()), commit_after=True)

            edges_create = EdgesCreate(
                edges=[
                    EdgeDefinition(
                        from_node_type="data_source",
                        from_node_id=data_source_id,
                        to_node_type="pipeline",
                        to_node_id=target_entity_id
                    ) for data_source_id in data_source_ids
                ] + [
                    EdgeDefinition(
                        from_node_type="dataset",
                        from_node_id=dataset_id,
                        to_node_type="pipeline",
                        to_node_id=target_entity_id
                    ) for dataset_id in dataset_ids
                ] + [
                    EdgeDefinition(
                        from_node_type="model_entity",
                        from_node_id=model_entity_id,
                        to_node_type="pipeline",
                        to_node_id=target_entity_id
                    ) for model_entity_id in model_entity_ids
                ]
            )
            if edges_create.edges:
                await create_edges(edges_create)

        await post_run_swe(client, RunSWERequest(
            run_id=run_id,
            project_id=run_record.project_id,
            conversation_id=run_record.conversation_id,
            target_pipeline_id=target_entity_id,
            prompt_content=run_record.plan_and_deliverable_description_for_user,
            input_data_source_ids=data_source_ids,
            input_dataset_ids=dataset_ids,
            input_model_entity_ids=model_entity_ids,
            input_analysis_ids=analysis_ids,
        ))

    elif run_record.type == "analysis":
        if target_entity_id is None:
            analysis_create = AnalysisCreate(
                name=run_record.run_name,
                description=run_record.plan_and_deliverable_description_for_user,
            )

            target_entity_id = (await create_analysis(analysis_create=analysis_create, user_id=user_id)).id
            await add_entity_to_project(user_id, AddEntityToProject(
                project_id=run_record.project_id,
                entity_type="analysis",
                entity_id=target_entity_id
            ))
            analysis_from_run_record = AnalysisFromRunInDB(
                run_id=run_id,
                analysis_id=target_entity_id,
                created_at=datetime.now(timezone.utc)
            )
            await execute(insert(analysis_from_run).values(analysis_from_run_record.model_dump()), commit_after=True)

            edges_create = EdgesCreate(
                edges=[
                    EdgeDefinition(
                        from_node_type="data_source",
                        from_node_id=data_source_id,
                        to_node_type="analysis",
                        to_node_id=target_entity_id
                    ) for data_source_id in data_source_ids
                ] + [
                    EdgeDefinition(
                        from_node_type="dataset",
                        from_node_id=dataset_id,
                        to_node_type="analysis",
                        to_node_id=target_entity_id
                    ) for dataset_id in dataset_ids
                ] + [
                    EdgeDefinition(
                        from_node_type="model_entity",
                        from_node_id=model_entity_id,
                        to_node_type="analysis",
                        to_node_id=target_entity_id
                    ) for model_entity_id in model_entity_ids
                ]
            )
            if edges_create.edges:
                await create_edges(edges_create)

        await post_run_analysis(client, RunAnalysisRequest(
            run_id=run_id,
            prompt_content=run_record.plan_and_deliverable_description_for_agent,
            target_analysis_id=target_entity_id,
            project_id=run_record.project_id,
            conversation_id=run_record.conversation_id,
            input_dataset_ids=dataset_ids,
            input_data_source_ids=data_source_ids,
            input_model_entity_ids=model_entity_ids,
            input_analysis_ids=analysis_ids
        ))

    await execute(run.update().where(run.c.id == run_id).values(status="running"), commit_after=True)
    return run_record


async def reject_run(run_id: uuid.UUID) -> RunInDB:
    run_record = RunInDB(**(await fetch_one(
        select(run).where(run.c.id == run_id)
    )))
    run_record.status = "rejected"
    await execute(run.update().where(run.c.id == run_id).values(status="rejected"), commit_after=True)
    return run_record


async def get_runs(
        user_id: uuid.UUID,
        filter_status: Optional[List[Literal["running",
                                             "pending",
                                             "completed",
                                             "failed",
                                             "rejected"]]] = None,
        run_ids: Optional[List[uuid.UUID]] = None,
        conversation_id: Optional[uuid.UUID] = None,
        project_id: Optional[uuid.UUID] = None,
) -> List[Run]:

    runs_query = select(run).where(run.c.user_id == user_id)

    if filter_status:
        runs_query = runs_query.where(run.c.status.in_(filter_status))
    if run_ids:
        runs_query = runs_query.where(run.c.id.in_(run_ids))
    if conversation_id:
        runs_query = runs_query.where(run.c.conversation_id == conversation_id)
    if project_id:
        runs_query = runs_query.where(run.c.project_id == project_id)

    runs = await fetch_all(runs_query)

    # Fetch all entity relationships for runs (inputs and outputs)
    run_id_list = [run_record["id"] for run_record in runs]

    # Input entities
    data_sources_in_runs = await fetch_all(
        select(data_source_in_run).where(
            data_source_in_run.c.run_id.in_(run_id_list))
    )
    datasets_in_runs = await fetch_all(
        select(dataset_in_run).where(dataset_in_run.c.run_id.in_(run_id_list))
    )
    model_entities_in_runs = await fetch_all(
        select(model_entity_in_run).where(
            model_entity_in_run.c.run_id.in_(run_id_list))
    )
    pipelines_in_runs = await fetch_all(
        select(pipeline_in_run).where(
            pipeline_in_run.c.run_id.in_(run_id_list))
    )
    analysis_in_runs = await fetch_all(
        select(analysis_in_run).where(
            analysis_in_run.c.run_id.in_(run_id_list))
    )
    # Output entities
    data_sources_from_runs = await fetch_all(
        select(data_source_from_run).where(
            data_source_from_run.c.run_id.in_(run_id_list))
    )
    datasets_from_runs = await fetch_all(
        select(dataset_from_run).where(
            dataset_from_run.c.run_id.in_(run_id_list))
    )
    model_entities_from_runs = await fetch_all(
        select(model_entity_from_run).where(
            model_entity_from_run.c.run_id.in_(run_id_list))
    )
    pipelines_from_runs = await fetch_all(
        select(pipeline_from_run).where(
            pipeline_from_run.c.run_id.in_(run_id_list))
    )
    analysis_from_runs = await fetch_all(
        select(analysis_from_run).where(
            analysis_from_run.c.run_id.in_(run_id_list))
    )
    run_records = []
    for run_record in runs:
        run_id = run_record["id"]

        # Build RunEntityIds for inputs
        inputs = RunEntityIds(
            data_source_ids=[r["data_source_id"]
                             for r in data_sources_in_runs if r["run_id"] == run_id],
            dataset_ids=[r["dataset_id"]
                         for r in datasets_in_runs if r["run_id"] == run_id],
            model_entity_ids=[r["model_entity_id"]
                              for r in model_entities_in_runs if r["run_id"] == run_id],
            pipeline_ids=[r["pipeline_id"]
                          for r in pipelines_in_runs if r["run_id"] == run_id],
            analysis_ids=[r["analysis_id"]
                          for r in analysis_in_runs if r["run_id"] == run_id]
        )

        # Build RunEntityIds for outputs
        outputs = RunEntityIds(
            data_source_ids=[r["data_source_id"]
                             for r in data_sources_from_runs if r["run_id"] == run_id],
            dataset_ids=[r["dataset_id"]
                         for r in datasets_from_runs if r["run_id"] == run_id],
            model_entity_ids=[r["model_entity_id"]
                              for r in model_entities_from_runs if r["run_id"] == run_id],
            pipeline_ids=[r["pipeline_id"]
                          for r in pipelines_from_runs if r["run_id"] == run_id],
            analysis_ids=[r["analysis_id"]
                          for r in analysis_from_runs if r["run_id"] == run_id]
        )

        run_records.append(
            Run(
                **run_record,
                inputs=inputs,
                outputs=outputs
            )
        )

    return run_records


async def update_run_status(run_id: uuid.UUID, run_status_update: RunStatusUpdate) -> RunInDB:
    run_record = RunInDB(**(await fetch_one(
        select(run).where(run.c.id == run_id)
    )))
    run_record.status = run_status_update.status

    await execute(run.update().where(run.c.id == run_id).values(status=run_status_update.status), commit_after=True)

    return run_record


async def get_run_messages(run_id: uuid.UUID) -> List[RunMessageInDB]:
    run_messages = await fetch_all(
        select(run_message).where(run_message.c.run_id == run_id)
    )
    return [RunMessageInDB(**message) for message in run_messages]


async def get_run_messages_pydantic(run_id: uuid.UUID, bytes: bool = False) -> list[Union[ModelMessage, RunPydanticMessageInDB]]:
    c = await fetch_all(
        select(run_pydantic_message).where(
            run_pydantic_message.c.run_id == run_id)
    )
    if bytes:
        return [RunPydanticMessageInDB(**message) for message in c]

    messages: list[ModelMessage] = []
    for message in c:
        messages.extend(
            ModelMessagesTypeAdapter.validate_json(message["message_list"]))

    return messages


async def create_run_message(run_message_create: RunMessageCreate) -> RunMessageInDB:

    run_message_record = RunMessageInDB(
        id=uuid.uuid4(),
        content=run_message_create.content,
        type=run_message_create.type,
        run_id=run_message_create.run_id,
        created_at=datetime.now(timezone.utc)
    )

    await execute(run_message.insert().values(run_message_record.model_dump()), commit_after=True)

    return run_message_record


async def create_run_message_pydantic(run_message_create_pydantic: RunMessageCreatePydantic) -> RunPydanticMessageInDB:
    run_pydantic_message_record = RunPydanticMessageInDB(
        id=uuid.uuid4(),
        run_id=run_message_create_pydantic.run_id,
        message_list=run_message_create_pydantic.content,
        created_at=datetime.now(timezone.utc)
    )

    await execute(run_pydantic_message.insert().values(run_pydantic_message_record.model_dump()), commit_after=True)

    return run_pydantic_message_record
