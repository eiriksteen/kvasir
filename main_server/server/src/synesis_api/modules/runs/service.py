import uuid
from typing import Literal, Optional, List, Union
from datetime import datetime, timezone
from sqlalchemy import select, insert
from pydantic_ai.messages import ModelMessagesTypeAdapter, ModelMessage

from synesis_api.database.service import fetch_all, execute, fetch_one
from synesis_api.modules.runs.schema import (
    RunInDB,
    DataSourceInRunInDB,
    RunCreate,
    DatasetInRunInDB,
    ModelEntityInRunInDB,
    PipelineInRunInDB,
    AnalysisFromRunInDB,
    PipelineFromRunInDB,
    AnalysisInRunInDB,
    Run,
    RunEntityIds,
    RunStatusUpdate,
    RunMessageCreate,
    RunMessageCreatePydantic,
    RunMessageInDB,
    RunPydanticMessageInDB,
)
from synesis_api.modules.runs.models import (
    run,
    run_pydantic_message,
    run_message
)


async def create_run(user_id: uuid.UUID, run_create: RunCreate) -> RunInDB:
    run_record = RunInDB(
        id=run_create.id or uuid.uuid4(),
        user_id=user_id,
        **run_create.model_dump(exclude={"id"}),
        started_at=datetime.now(timezone.utc),
        status=run_create.initial_status
    )

    data_sources_in_run_records = []
    datasets_in_run_records = []
    model_instantiatedies_in_run_records = []
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
    for model_instantiated_id in run_create.models_instantiated_in_run:
        model_instantiatedies_in_run_records.append(ModelEntityInRunInDB(
            run_id=run_record.id,
            model_instantiated_id=model_instantiated_id,
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

    return run_record


async def launch_run(user_id: uuid.UUID, run_id: uuid.UUID):
    # TODO: Function needs to be reimplemented with new ontology interface
    pass
    # run_record = RunInDB(**(await fetch_one(select(run).where(run.c.id == run_id))))
    # run_record.status = "running"
    # data_source_ids = [rec["data_source_id"] for rec in await fetch_all(
    #     select(data_source_in_run).where(
    #         data_source_in_run.c.run_id == run_id))]
    # dataset_ids = [rec["dataset_id"] for rec in await fetch_all(
    #     select(dataset_in_run).where(
    #         dataset_in_run.c.run_id == run_id))]
    # model_instantiated_ids = [rec["model_instantiated_id"] for rec in await fetch_all(
    #     select(model_instantiated_in_run).where(
    #         model_instantiated_in_run.c.run_id == run_id))]
    # analysis_ids = [rec["analysis_id"] for rec in await fetch_all(
    #     select(analysis_in_run).where(
    #         analysis_in_run.c.run_id == run_id))]
    # # pipeline_ids = [rec["pipeline_id"] for rec in await fetch_all(
    # #     select(pipeline_in_run).where(
    # #         pipeline_in_run.c.run_id == run_id))]

    # analysis_from_run_record = await fetch_one(
    #     select(analysis_from_run).where(
    #         analysis_from_run.c.run_id == run_id))
    # pipeline_from_run_record = await fetch_one(
    #     select(pipeline_from_run).where(
    #         pipeline_from_run.c.run_id == run_id))

    # if analysis_from_run_record:
    #     target_entity_id = analysis_from_run_record["analysis_id"]
    # elif pipeline_from_run_record:
    #     target_entity_id = pipeline_from_run_record["pipeline_id"]
    # else:
    #     target_entity_id = None
    # # else:
    # #     raise RuntimeError(
    # #         "No associated entity found for run (the analysis or pipeline entity must be created before the run is launched. The orchestrator should do this automatically. )")

    # # Create ontology instance for entity and edge insertion
    # ontology = await create_ontology_for_user(user_id, run_record.project_id)

    # if run_record.type == "swe":
    #     if target_entity_id is None:
    #         pipeline_create = PipelineCreate(
    #             name=run_record.run_name,
    #             description=run_record.plan_and_deliverable_description_for_agent,
    #             # input_data_source_ids=data_source_ids,
    #             # input_dataset_ids=dataset_ids,
    #             # input_model_entity_ids=model_instantiated_ids,
    #             # input_analysis_ids=analysis_ids
    #         )
    #
    #         # Use ontology interface to insert pipeline (without edges initially)
    #         pipeline_obj = await ontology.insert_pipeline(pipeline_create, [])
    #         target_entity_id = pipeline_obj.id
    #
    #         # Now build edges with the actual pipeline ID
    #         edges = [
    #             EdgeDefinition(
    #                 from_node_type="data_source",
    #                 from_node_id=data_source_id,
    #                 to_node_type="pipeline",
    #                 to_node_id=target_entity_id
    #             ) for data_source_id in data_source_ids
    #         ] + [
    #             EdgeDefinition(
    #                 from_node_type="dataset",
    #                 from_node_id=dataset_id,
    #                 to_node_type="pipeline",
    #                 to_node_id=target_entity_id
    #             ) for dataset_id in dataset_ids
    #         ] + [
    #             EdgeDefinition(
    #                 from_node_type="model_instantiated",
    #                 from_node_id=model_instantiated_id,
    #                 to_node_type="pipeline",
    #                 to_node_id=target_entity_id
    #             ) for model_instantiated_id in model_instantiated_ids
    #         ]
    #
    #         # Create edges if there are any
    #         if edges:
    #             await ontology.graph.create_edges(edges)
    #
    #         pipeline_from_run_record = PipelineFromRunInDB(
    #             run_id=run_id,
    #             pipeline_id=target_entity_id,
    #             created_at=datetime.now(timezone.utc)
    #         )
    #         await execute(insert(pipeline_from_run).values(pipeline_from_run_record.model_dump()), commit_after=True)

    #     await post_run_swe(client, RunSWERequest(
    #         run_id=run_id,
    #         project_id=run_record.project_id,
    #         conversation_id=run_record.conversation_id,
    #         target_pipeline_id=target_entity_id,
    #         prompt_content=run_record.plan_and_deliverable_description_for_user,
    #         input_data_source_ids=data_source_ids,
    #         input_dataset_ids=dataset_ids,
    #         input_model_entity_ids=model_instantiated_ids,
    #         input_analysis_ids=analysis_ids,
    #     ))

    # elif run_record.type == "analysis":
    #     if target_entity_id is None:
    #         analysis_create = AnalysisCreate(
    #             name=run_record.run_name,
    #             description=run_record.plan_and_deliverable_description_for_user,
    #         )

    #         # Use ontology interface to insert analysis (without edges initially)
    #         analysis_obj = await ontology.insert_analysis(analysis_create, [])
    #         target_entity_id = analysis_obj.id
    #
    #         # Now build edges with the actual analysis ID
    #         edges = [
    #             EdgeDefinition(
    #                 from_node_type="data_source",
    #                 from_node_id=data_source_id,
    #                 to_node_type="analysis",
    #                 to_node_id=target_entity_id
    #             ) for data_source_id in data_source_ids
    #         ] + [
    #             EdgeDefinition(
    #                 from_node_type="dataset",
    #                 from_node_id=dataset_id,
    #                 to_node_type="analysis",
    #                 to_node_id=target_entity_id
    #             ) for dataset_id in dataset_ids
    #         ] + [
    #             EdgeDefinition(
    #                 from_node_type="model_instantiated",
    #                 from_node_id=model_instantiated_id,
    #                 to_node_type="analysis",
    #                 to_node_id=target_entity_id
    #             ) for model_instantiated_id in model_instantiated_ids
    #         ]
    #
    #         # Create edges if there are any
    #         if edges:
    #             await ontology.graph.create_edges(edges)
    #
    #         analysis_from_run_record = AnalysisFromRunInDB(
    #             run_id=run_id,
    #             analysis_id=target_entity_id,
    #             created_at=datetime.now(timezone.utc)
    #         )
    #         await execute(insert(analysis_from_run).values(analysis_from_run_record.model_dump()), commit_after=True)

    #     await post_run_analysis(client, RunAnalysisRequest(
    #         run_id=run_id,
    #         prompt_content=run_record.plan_and_deliverable_description_for_agent,
    #         target_analysis_id=target_entity_id,
    #         project_id=run_record.project_id,
    #         conversation_id=run_record.conversation_id,
    #         input_dataset_ids=dataset_ids,
    #         input_data_source_ids=data_source_ids,
    #         input_model_entity_ids=model_instantiated_ids,
    #         input_analysis_ids=analysis_ids
    #     ))

    # await execute(run.update().where(run.c.id == run_id).values(status="running"), commit_after=True)
    # return run_record


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
    run_objs = [
        Run(**run_record) for run_record in runs
    ]

    return run_objs


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
