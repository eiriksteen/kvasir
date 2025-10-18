import uuid
from datetime import datetime, timezone
from typing import Literal, Optional, List, Union
from sqlalchemy import select, insert
from pydantic_ai.messages import ModelMessagesTypeAdapter, ModelMessage

from synesis_api.client import MainServerClient, post_run_data_integration, post_run_pipeline_agent, post_run_model_integration
from synesis_api.database.service import fetch_all, execute, fetch_one
from synesis_schemas.main_server import (
    RunInDB,
    RunPydanticMessageInDB,
    RunMessageInDB,
    DataSourceInRunInDB,
    Run,
    RunCreate,
    RunMessageCreate,
    RunMessageCreatePydantic,
    RunSpecificationInDB,
    DatasetInRunInDB,
    ModelEntityInRunInDB,
    PipelineInRunInDB,
    RunEntityIds,
    RunStatusUpdate
)
from synesis_schemas.project_server import RunDataIntegrationAgentRequest, RunPipelineAgentRequest, RunModelIntegrationAgentRequest
from synesis_api.modules.runs.models import (
    run_specification,
    run,
    run_pydantic_message,
    run_message,
    data_source_in_run,
    dataset_in_run,
    model_entity_in_run,
    pipeline_in_run,
    data_source_from_run,
    dataset_from_run,
    model_entity_from_run,
    pipeline_from_run,
    run_summary
)


async def create_run(user_id: uuid.UUID, run_create: RunCreate) -> RunInDB:
    run_record = RunInDB(
        id=uuid.uuid4(),
        user_id=user_id,
        **run_create.model_dump(),
        started_at=datetime.now(timezone.utc),
        status=run_create.initial_status
    )

    run_specification_record = None
    if run_create.spec:
        run_specification_record = RunSpecificationInDB(
            id=uuid.uuid4(),
            run_id=run_record.id,
            **run_create.spec.model_dump(),
            created_at=datetime.now(timezone.utc),
            updated_at=datetime.now(timezone.utc)
        )

    data_sources_in_run_records = []
    datasets_in_run_records = []
    model_entities_in_run_records = []
    pipelines_in_run_records = []
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

    await execute(run.insert().values(run_record.model_dump()), commit_after=True)

    if run_specification_record:
        await execute(run_specification.insert().values(run_specification_record.model_dump()), commit_after=True)
    if data_sources_in_run_records:
        await execute(insert(data_source_in_run).values(data_sources_in_run_records), commit_after=True)
    if datasets_in_run_records:
        await execute(insert(dataset_in_run).values(datasets_in_run_records), commit_after=True)
    if model_entities_in_run_records:
        await execute(insert(model_entity_in_run).values(model_entities_in_run_records), commit_after=True)
    if pipelines_in_run_records:
        await execute(insert(pipeline_in_run).values(pipelines_in_run_records), commit_after=True)

    return run_record


async def launch_run(client: MainServerClient, run_id: uuid.UUID):
    run_record = RunInDB(**(await fetch_one(select(run).where(run.c.id == run_id))))
    run_record.status = "running"
    run_spec = RunSpecificationInDB(**(await fetch_one(
        select(run_specification).where(
            run_specification.c.run_id == run_id))))
    data_source_ids = [rec["data_source_id"] for rec in await fetch_all(
        select(data_source_in_run).where(
            data_source_in_run.c.run_id == run_id))]
    dataset_ids = [rec["dataset_id"] for rec in await fetch_all(
        select(dataset_in_run).where(
            dataset_in_run.c.run_id == run_id))]
    model_entity_ids = [rec["model_entity_id"] for rec in await fetch_all(
        select(model_entity_in_run).where(
            model_entity_in_run.c.run_id == run_id))]
    pipeline_ids = [rec["pipeline_id"] for rec in await fetch_all(
        select(pipeline_in_run).where(
            pipeline_in_run.c.run_id == run_id))]

    if run_record.type == "data_integration":
        await post_run_data_integration(client, RunDataIntegrationAgentRequest(
            run_id=run_id,
            project_id=run_record.project_id,
            conversation_id=run_record.conversation_id,
            data_source_ids=data_source_ids,
            dataset_ids=dataset_ids,
            model_entity_ids=model_entity_ids,
            pipeline_ids=pipeline_ids,
            prompt_content=run_spec.plan_and_deliverable_description_for_agent
        ))

    elif run_record.type == "pipeline":
        await post_run_pipeline_agent(client, RunPipelineAgentRequest(
            run_id=run_id,
            project_id=run_record.project_id,
            conversation_id=run_record.conversation_id,
            prompt_content=run_spec.plan_and_deliverable_description_for_agent,
            input_dataset_ids=dataset_ids,
            input_model_entity_ids=model_entity_ids
        ))

    elif run_record.type == "model_integration":
        await post_run_model_integration(client, RunModelIntegrationAgentRequest(
            run_id=run_id,
            project_id=run_record.project_id,
            conversation_id=run_record.conversation_id,
            prompt_content=run_spec.plan_and_deliverable_description_for_agent,
            # TODO: Make it based on user input
            public=False
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
        exclude_swe: bool = True) -> List[Run]:

    runs_query = select(run).where(run.c.user_id == user_id)

    if filter_status:
        runs_query = runs_query.where(run.c.status.in_(filter_status))
    if run_ids:
        runs_query = runs_query.where(run.c.id.in_(run_ids))
    if conversation_id:
        runs_query = runs_query.where(run.c.conversation_id == conversation_id)

    if exclude_swe:
        runs_query = runs_query.where(run.c.type != "swe")

    runs = await fetch_all(runs_query)

    # Fetch run specifications
    run_spec_records = await fetch_all(
        select(run_specification).where(
            run_specification.c.run_id.in_(
                [run_record["id"] for run_record in runs])
        )
    )

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

    run_records = []
    for run_record in runs:
        run_id = run_record["id"]

        # Get spec using next() iterator
        spec = next(
            (RunSpecificationInDB(**rec)
             for rec in run_spec_records if rec["run_id"] == run_id),
            None
        )

        # Build RunEntityIds for inputs
        inputs = RunEntityIds(
            data_source_ids=[r["data_source_id"]
                             for r in data_sources_in_runs if r["run_id"] == run_id],
            dataset_ids=[r["dataset_id"]
                         for r in datasets_in_runs if r["run_id"] == run_id],
            model_entity_ids=[r["model_entity_id"]
                              for r in model_entities_in_runs if r["run_id"] == run_id],
            pipeline_ids=[r["pipeline_id"]
                          for r in pipelines_in_runs if r["run_id"] == run_id]
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
                          for r in pipelines_from_runs if r["run_id"] == run_id]
        )

        run_records.append(
            Run(
                **run_record,
                spec=spec,
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

    if run_status_update.summary:
        await execute(run_summary.insert().values(run_id=run_id, summary=run_status_update.summary), commit_after=True)

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


async def get_run_summary(run_id: uuid.UUID) -> str | None:
    run_summary_record = await fetch_one(
        select(run_summary).where(run_summary.c.run_id == run_id)
    )
    if not run_summary_record:
        return None
    return run_summary_record["summary"]
