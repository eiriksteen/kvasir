import uuid
from datetime import datetime, timezone
from typing import List, Optional, Literal
from sqlalchemy import select, insert
from fastapi import HTTPException

from synesis_api.database.service import fetch_all, execute, fetch_one
from synesis_api.modules.pipeline.models import (
    pipeline,
    pipeline_implementation,
    function_in_pipeline,
    data_source_supported_in_pipeline,
    dataset_supported_in_pipeline,
    model_entity_supported_in_pipeline,
    pipeline_run,
    dataset_in_pipeline_run,
    data_source_in_pipeline_run,
    model_entity_in_pipeline_run,
    pipeline_run_output_dataset,
    pipeline_run_output_model_entity,
    pipeline_run_output_data_source
)
from synesis_api.modules.function.service import get_functions
from synesis_schemas.main_server import (
    PipelineInDB,
    PipelineImplementationInDB,
    Pipeline,
    PipelineImplementation,
    PipelineImplementationCreate,
    PipelineRunEntities,
    PipelineRun,
    ModelEntitySupportedInPipelineInDB,
    DataSourceSupportedInPipelineInDB,
    DatasetSupportedInPipelineInDB,
    PipelineRunInDB,
    PipelineRunOutputDatasetInDB,
    PipelineRunOutputModelEntityInDB,
    PipelineRunOutputDataSourceInDB,
    PipelineRunOutputsCreate,
    PipelineCreate,
    FunctionInPipelineInDB,
    RunPipelineRequest,
    DatasetInPipelineRunInDB,
    DataSourceInPipelineRunInDB,
    ModelEntityInPipelineRunInDB,
)
from synesis_api.modules.pipeline.description import get_pipeline_description


async def create_pipeline(user_id: uuid.UUID, pipeline_create: PipelineCreate) -> PipelineInDB:
    pipeline_record = PipelineInDB(
        id=uuid.uuid4(),
        user_id=user_id,
        **pipeline_create.model_dump(),
        created_at=datetime.now(timezone.utc),
        updated_at=datetime.now(timezone.utc)
    )

    data_source_supported_in_pipeline_records = [DataSourceSupportedInPipelineInDB(
        pipeline_id=pipeline_record.id,
        data_source_id=data_source_id,
        created_at=datetime.now(timezone.utc),
        updated_at=datetime.now(timezone.utc)
    ).model_dump() for data_source_id in pipeline_create.supported_inputs.data_source_ids]

    dataset_supported_in_pipeline_records = [DatasetSupportedInPipelineInDB(
        pipeline_id=pipeline_record.id,
        dataset_id=dataset_id,
        created_at=datetime.now(timezone.utc),
        updated_at=datetime.now(timezone.utc)
    ).model_dump() for dataset_id in pipeline_create.supported_inputs.dataset_ids]

    model_entity_supported_in_pipeline_records = [ModelEntitySupportedInPipelineInDB(
        pipeline_id=pipeline_record.id,
        model_entity_id=model_entity_id,
        created_at=datetime.now(timezone.utc),
        updated_at=datetime.now(timezone.utc)
    ).model_dump() for model_entity_id in pipeline_create.supported_inputs.model_entity_ids]

    await execute(insert(pipeline).values(pipeline_record.model_dump()), commit_after=True)

    if len(data_source_supported_in_pipeline_records) > 0:
        await execute(insert(data_source_supported_in_pipeline).values(data_source_supported_in_pipeline_records), commit_after=True)
    if len(dataset_supported_in_pipeline_records) > 0:
        await execute(insert(dataset_supported_in_pipeline).values(dataset_supported_in_pipeline_records), commit_after=True)
    if len(model_entity_supported_in_pipeline_records) > 0:
        await execute(insert(model_entity_supported_in_pipeline).values(model_entity_supported_in_pipeline_records), commit_after=True)

    return pipeline_record


async def create_pipeline_implementation(user_id: uuid.UUID, pipeline_implementation_create: PipelineImplementationCreate) -> PipelineImplementationInDB:

    if pipeline_implementation_create.pipeline_id:
        pipeline_record = await fetch_one(select(pipeline.c.id).where(pipeline.c.id == pipeline_implementation_create.pipeline_id))
        if not pipeline_record:
            raise HTTPException(
                status_code=404, detail=f"Pipeline with id {pipeline_implementation_create.pipeline_id} not found")
        pipeline_id = pipeline_record["id"]
    else:
        pipeline_record = await create_pipeline(user_id, pipeline_implementation_create.pipeline_create)
        pipeline_id = pipeline_record.id

    pipeline_obj = PipelineImplementationInDB(
        id=pipeline_id,
        **pipeline_implementation_create.model_dump(),
        created_at=datetime.now(timezone.utc),
        updated_at=datetime.now(timezone.utc)
    )

    await execute(insert(pipeline_implementation).values(**pipeline_obj.model_dump()), commit_after=True)

    fn_in_pipeline_records = [
        FunctionInPipelineInDB(
            pipeline_id=pipeline_obj.id,
            function_id=function_id,
            created_at=datetime.now(timezone.utc),
            updated_at=datetime.now(timezone.utc)
        ).model_dump() for function_id in pipeline_implementation_create.function_ids
    ]

    if len(fn_in_pipeline_records) > 0:
        await execute(insert(function_in_pipeline).values(fn_in_pipeline_records), commit_after=True)

    return pipeline_obj


async def get_user_pipelines(
    user_id: uuid.UUID,
    pipeline_ids: Optional[List[uuid.UUID]] = None
) -> List[Pipeline]:

    pipeline_query = select(pipeline).where(pipeline.c.user_id == user_id)
    if pipeline_ids is not None:
        pipeline_query = pipeline_query.where(pipeline.c.id.in_(pipeline_ids))

    pipelines = await fetch_all(pipeline_query)
    pipeline_ids = [p["id"] for p in pipelines]

    pipeline_implementation_query = select(pipeline_implementation).where(
        pipeline_implementation.c.id.in_(pipeline_ids))

    pipeline_implementations = await fetch_all(pipeline_implementation_query)

    # pipeline runs
    pipeline_runs_query = select(pipeline_run).where(
        pipeline_run.c.pipeline_id.in_(pipeline_ids))
    pipeline_runs = await fetch_all(pipeline_runs_query)
    pipeline_run_ids = [r["id"] for r in pipeline_runs]

    # functions in the pipelines
    functions_in_pipelines_query = select(function_in_pipeline).where(
        function_in_pipeline.c.pipeline_id.in_(pipeline_ids))
    functions_in_pipelines = await fetch_all(functions_in_pipelines_query)

    function_records = await get_functions(
        [f["function_id"] for f in functions_in_pipelines])

    # supported inputs (what can be used)
    supported_data_sources_query = select(data_source_supported_in_pipeline).where(
        data_source_supported_in_pipeline.c.pipeline_id.in_(pipeline_ids))
    supported_data_sources = await fetch_all(supported_data_sources_query)

    supported_datasets_query = select(dataset_supported_in_pipeline).where(
        dataset_supported_in_pipeline.c.pipeline_id.in_(pipeline_ids))
    supported_datasets = await fetch_all(supported_datasets_query)

    supported_model_entities_query = select(model_entity_supported_in_pipeline).where(
        model_entity_supported_in_pipeline.c.pipeline_id.in_(pipeline_ids))
    supported_model_entities = await fetch_all(supported_model_entities_query)

    # run inputs (what was actually used in each run)
    run_input_datasets_query = select(dataset_in_pipeline_run).where(
        dataset_in_pipeline_run.c.pipeline_run_id.in_(pipeline_run_ids)) if pipeline_run_ids else []
    run_input_datasets = await fetch_all(run_input_datasets_query) if pipeline_run_ids else []

    run_input_data_sources_query = select(data_source_in_pipeline_run).where(
        data_source_in_pipeline_run.c.pipeline_run_id.in_(pipeline_run_ids)) if pipeline_run_ids else []
    run_input_data_sources = await fetch_all(run_input_data_sources_query) if pipeline_run_ids else []

    run_input_model_entities_query = select(model_entity_in_pipeline_run).where(
        model_entity_in_pipeline_run.c.pipeline_run_id.in_(pipeline_run_ids)) if pipeline_run_ids else []
    run_input_model_entities = await fetch_all(run_input_model_entities_query) if pipeline_run_ids else []

    # run outputs (what was produced by each run)
    run_output_datasets_query = select(pipeline_run_output_dataset).where(
        pipeline_run_output_dataset.c.pipeline_run_id.in_(pipeline_run_ids)) if pipeline_run_ids else []
    run_output_datasets = await fetch_all(run_output_datasets_query) if pipeline_run_ids else []

    run_output_model_entities_query = select(pipeline_run_output_model_entity).where(
        pipeline_run_output_model_entity.c.pipeline_run_id.in_(pipeline_run_ids)) if pipeline_run_ids else []
    run_output_model_entities = await fetch_all(run_output_model_entities_query) if pipeline_run_ids else []

    run_output_data_sources_query = select(pipeline_run_output_data_source).where(
        pipeline_run_output_data_source.c.pipeline_run_id.in_(pipeline_run_ids)) if pipeline_run_ids else []
    run_output_data_sources = await fetch_all(run_output_data_sources_query) if pipeline_run_ids else []

    output_objs = []
    for pipe_id in pipeline_ids:
        pipe_obj = PipelineInDB(**next(
            iter([p for p in pipelines if p["id"] == pipe_id])))

        # Build supported inputs
        supported_data_source_ids = [s["data_source_id"]
                                     for s in supported_data_sources if s["pipeline_id"] == pipe_id]
        supported_dataset_ids = [s["dataset_id"]
                                 for s in supported_datasets if s["pipeline_id"] == pipe_id]
        supported_model_entity_ids = [s["model_entity_id"]
                                      for s in supported_model_entities if s["pipeline_id"] == pipe_id]

        supported_inputs = PipelineRunEntities(
            data_source_ids=supported_data_source_ids,
            dataset_ids=supported_dataset_ids,
            model_entity_ids=supported_model_entity_ids,
        )

        pipe_implementation_record = next(iter([
            p for p in pipeline_implementations if p["id"] == pipe_id]), None)

        pipeline_implementation_obj = None
        runs_objs = []
        if pipe_implementation_record:
            runs_records = [
                r for r in pipeline_runs if r["pipeline_id"] == pipe_id]

            # Build run objects with inputs and outputs
            for run_record in runs_records:
                run_id = run_record["id"]

                # Build run inputs
                run_dataset_ids = [
                    r["dataset_id"] for r in run_input_datasets if r["pipeline_run_id"] == run_id]
                run_data_source_ids = [
                    r["data_source_id"] for r in run_input_data_sources if r["pipeline_run_id"] == run_id]
                run_model_entity_ids = [
                    r["model_entity_id"] for r in run_input_model_entities if r["pipeline_run_id"] == run_id]

                run_inputs = PipelineRunEntities(
                    dataset_ids=run_dataset_ids,
                    data_source_ids=run_data_source_ids,
                    model_entity_ids=run_model_entity_ids,
                )

                # Build run outputs
                run_output_dataset_ids = [
                    r["dataset_id"] for r in run_output_datasets if r["pipeline_run_id"] == run_id]
                run_output_data_source_ids = [
                    r["data_source_id"] for r in run_output_data_sources if r["pipeline_run_id"] == run_id]
                run_output_model_entity_ids = [
                    r["model_entity_id"] for r in run_output_model_entities if r["pipeline_run_id"] == run_id]

                run_outputs = PipelineRunEntities(
                    dataset_ids=run_output_dataset_ids,
                    data_source_ids=run_output_data_source_ids,
                    model_entity_ids=run_output_model_entity_ids,
                )

                runs_objs.append(PipelineRun(
                    **run_record,
                    inputs=run_inputs,
                    outputs=run_outputs,
                ))

            function_ids_in_pipeline = [
                f["function_id"] for f in functions_in_pipelines if f["pipeline_id"] == pipe_id]
            functions_records = [
                f for f in function_records if f.id in function_ids_in_pipeline]

            pipeline_implementation_obj = PipelineImplementation(
                **pipe_implementation_record,
                functions=functions_records
            )

        pipeline_description = get_pipeline_description(
            pipeline_in_db=pipe_obj,
            supported_inputs=supported_inputs,
            runs=runs_objs,
            implementation=pipeline_implementation_obj
        )

        output_objs.append(Pipeline(
            **pipe_obj.model_dump(),
            supported_inputs=supported_inputs,
            runs=runs_objs,
            implementation=pipeline_implementation_obj,
            description_for_agent=pipeline_description
        ))

    return output_objs


async def create_pipeline_run(run_request: RunPipelineRequest) -> PipelineRunInDB:
    pipeline_run_obj = PipelineRunInDB(
        id=uuid.uuid4(),
        **run_request.model_dump(),
        output_variables={},
        status="running",
        start_time=datetime.now(timezone.utc),
        created_at=datetime.now(timezone.utc),
        updated_at=datetime.now(timezone.utc))
    await execute(insert(pipeline_run).values(pipeline_run_obj.model_dump()), commit_after=True)

    # Create input associations
    dataset_input_records = [DatasetInPipelineRunInDB(
        pipeline_run_id=pipeline_run_obj.id,
        dataset_id=dataset_id,
        created_at=datetime.now(timezone.utc),
        updated_at=datetime.now(timezone.utc)
    ).model_dump() for dataset_id in run_request.inputs.dataset_ids]

    data_source_input_records = [DataSourceInPipelineRunInDB(
        pipeline_run_id=pipeline_run_obj.id,
        data_source_id=data_source_id,
        created_at=datetime.now(timezone.utc),
        updated_at=datetime.now(timezone.utc)
    ).model_dump() for data_source_id in run_request.inputs.data_source_ids]

    model_entity_input_records = [ModelEntityInPipelineRunInDB(
        pipeline_run_id=pipeline_run_obj.id,
        model_entity_id=model_entity_id,
        created_at=datetime.now(timezone.utc),
        updated_at=datetime.now(timezone.utc)
    ).model_dump() for model_entity_id in run_request.inputs.model_entity_ids]

    if len(dataset_input_records) > 0:
        await execute(insert(dataset_in_pipeline_run).values(dataset_input_records), commit_after=True)
    if len(data_source_input_records) > 0:
        await execute(insert(data_source_in_pipeline_run).values(data_source_input_records), commit_after=True)
    if len(model_entity_input_records) > 0:
        await execute(insert(model_entity_in_pipeline_run).values(model_entity_input_records), commit_after=True)

    return pipeline_run_obj


async def get_pipeline_runs(
    user_id: uuid.UUID,
    only_running: bool = False,
    pipeline_ids: Optional[List[uuid.UUID]] = None,
    run_ids: Optional[List[uuid.UUID]] = None
) -> List[PipelineRun]:

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
    pipeline_run_ids = [r["id"] for r in pipeline_runs]

    if not pipeline_run_ids:
        return []

    # Fetch run inputs
    run_input_datasets = await fetch_all(
        select(dataset_in_pipeline_run).where(
            dataset_in_pipeline_run.c.pipeline_run_id.in_(pipeline_run_ids)))

    run_input_data_sources = await fetch_all(
        select(data_source_in_pipeline_run).where(
            data_source_in_pipeline_run.c.pipeline_run_id.in_(pipeline_run_ids)))

    run_input_model_entities = await fetch_all(
        select(model_entity_in_pipeline_run).where(
            model_entity_in_pipeline_run.c.pipeline_run_id.in_(pipeline_run_ids)))

    # Fetch run outputs
    run_output_datasets = await fetch_all(
        select(pipeline_run_output_dataset).where(
            pipeline_run_output_dataset.c.pipeline_run_id.in_(pipeline_run_ids)))

    run_output_data_sources = await fetch_all(
        select(pipeline_run_output_data_source).where(
            pipeline_run_output_data_source.c.pipeline_run_id.in_(pipeline_run_ids)))

    run_output_model_entities = await fetch_all(
        select(pipeline_run_output_model_entity).where(
            pipeline_run_output_model_entity.c.pipeline_run_id.in_(pipeline_run_ids)))

    # Build PipelineRun objects
    result = []
    for run in pipeline_runs:
        run_id = run["id"]

        # Build inputs
        inputs = PipelineRunEntities(
            dataset_ids=[r["dataset_id"]
                         for r in run_input_datasets if r["pipeline_run_id"] == run_id],
            data_source_ids=[r["data_source_id"]
                             for r in run_input_data_sources if r["pipeline_run_id"] == run_id],
            model_entity_ids=[r["model_entity_id"]
                              for r in run_input_model_entities if r["pipeline_run_id"] == run_id],
        )

        # Build outputs
        outputs = PipelineRunEntities(
            dataset_ids=[r["dataset_id"]
                         for r in run_output_datasets if r["pipeline_run_id"] == run_id],
            data_source_ids=[r["data_source_id"]
                             for r in run_output_data_sources if r["pipeline_run_id"] == run_id],
            model_entity_ids=[r["model_entity_id"]
                              for r in run_output_model_entities if r["pipeline_run_id"] == run_id],
        )

        result.append(PipelineRun(
            **run,
            inputs=inputs,
            outputs=outputs,
        ))

    return result


async def update_pipeline_run_status(pipeline_run_id: uuid.UUID, status: Literal["running", "completed", "failed"]) -> PipelineRunInDB:
    pipeline_run_obj = await fetch_one(select(pipeline_run).where(pipeline_run.c.id == pipeline_run_id))
    await execute(pipeline_run.update().where(pipeline_run.c.id == pipeline_run_id).values(status=status), commit_after=True)
    pipeline_run_obj["status"] = status
    return PipelineRunInDB(**pipeline_run_obj)


async def create_pipeline_run_outputs(pipeline_run_id: uuid.UUID, request: PipelineRunOutputsCreate) -> None:
    # Create dataset outputs
    dataset_output_records = [PipelineRunOutputDatasetInDB(
        pipeline_run_id=pipeline_run_id,
        dataset_id=dataset_id,
        created_at=datetime.now(timezone.utc),
        updated_at=datetime.now(timezone.utc)
    ).model_dump() for dataset_id in request.dataset_ids]

    # Create model entity outputs
    model_entity_output_records = [PipelineRunOutputModelEntityInDB(
        pipeline_run_id=pipeline_run_id,
        model_entity_id=model_entity_id,
        created_at=datetime.now(timezone.utc),
        updated_at=datetime.now(timezone.utc)
    ).model_dump() for model_entity_id in request.model_entity_ids]

    # Create data source outputs
    data_source_output_records = [PipelineRunOutputDataSourceInDB(
        pipeline_run_id=pipeline_run_id,
        data_source_id=data_source_id,
        created_at=datetime.now(timezone.utc),
        updated_at=datetime.now(timezone.utc)
    ).model_dump() for data_source_id in request.data_source_ids]

    # Insert all output records
    if len(dataset_output_records) > 0:
        await execute(insert(pipeline_run_output_dataset).values(dataset_output_records), commit_after=True)
    if len(model_entity_output_records) > 0:
        await execute(insert(pipeline_run_output_model_entity).values(model_entity_output_records), commit_after=True)
    if len(data_source_output_records) > 0:
        await execute(insert(pipeline_run_output_data_source).values(data_source_output_records), commit_after=True)
