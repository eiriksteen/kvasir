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
    data_source_in_pipeline,
    dataset_in_pipeline,
    model_entity_in_pipeline,
    pipeline_run,
    pipeline_output_dataset,
    pipeline_output_model_entity
)
from synesis_api.modules.function.service import get_functions
from synesis_schemas.main_server import (
    PipelineInDB,
    PipelineImplementationInDB,
    Pipeline,
    PipelineImplementation,
    PipelineImplementationCreate,
    PipelineInputEntities,
    PipelineOutputEntities,
    ModelEntityInPipelineInDB,
    PipelineRunInDB,
    PipelineOutputDatasetInDB,
    PipelineOutputModelEntityInDB,
    PipelineRunDatasetOutputCreate,
    PipelineRunModelEntityOutputCreate,
    PipelineCreate,
    DataSourceInPipelineInDB,
    DatasetInPipelineInDB,
    ModelEntityInPipelineInDB,
    FunctionInPipelineInDB
)
from synesis_api.modules.code.service import create_script, get_scripts


async def create_pipeline(user_id: uuid.UUID, pipeline_create: PipelineCreate) -> PipelineInDB:
    pipeline_record = PipelineInDB(
        id=uuid.uuid4(),
        user_id=user_id,
        **pipeline_create.model_dump(),
        created_at=datetime.now(timezone.utc),
        updated_at=datetime.now(timezone.utc)
    )

    data_source_in_pipeline_records = [DataSourceInPipelineInDB(
        pipeline_id=pipeline_record.id,
        data_source_id=data_source_id,
        created_at=datetime.now(timezone.utc),
        updated_at=datetime.now(timezone.utc)
    ).model_dump() for data_source_id in pipeline_create.input_data_source_ids]

    dataset_in_pipeline_records = [DatasetInPipelineInDB(
        pipeline_id=pipeline_record.id,
        dataset_id=dataset_id,
        created_at=datetime.now(timezone.utc),
        updated_at=datetime.now(timezone.utc)
    ).model_dump() for dataset_id in pipeline_create.input_dataset_ids]

    model_entity_in_pipeline_records = [ModelEntityInPipelineInDB(
        pipeline_id=pipeline_record.id,
        model_entity_id=model_entity_id,
        created_at=datetime.now(timezone.utc),
        updated_at=datetime.now(timezone.utc)
    ).model_dump() for model_entity_id in pipeline_create.input_model_entity_ids]

    await execute(insert(pipeline).values(pipeline_record.model_dump()), commit_after=True)

    if len(data_source_in_pipeline_records) > 0:
        await execute(insert(data_source_in_pipeline).values(data_source_in_pipeline_records), commit_after=True)
    if len(dataset_in_pipeline_records) > 0:
        await execute(insert(dataset_in_pipeline).values(dataset_in_pipeline_records), commit_after=True)
    if len(model_entity_in_pipeline_records) > 0:
        await execute(insert(model_entity_in_pipeline).values(model_entity_in_pipeline_records), commit_after=True)

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

    implementation_script_record = await create_script(user_id, pipeline_implementation_create.implementation_script_create)

    pipeline_obj = PipelineImplementationInDB(
        id=pipeline_id,
        implementation_script_id=implementation_script_record.id,
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
    pipeline_ids = [p["id"] for p in pipeline_implementations]

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

    # inputs
    data_sources_query = select(data_source_in_pipeline).where(
        data_source_in_pipeline.c.pipeline_id.in_(pipeline_ids))
    data_sources = await fetch_all(data_sources_query)

    datasets_query = select(dataset_in_pipeline).where(
        dataset_in_pipeline.c.pipeline_id.in_(pipeline_ids))
    datasets = await fetch_all(datasets_query)

    model_entities_query = select(model_entity_in_pipeline).where(
        model_entity_in_pipeline.c.pipeline_id.in_(pipeline_ids))

    model_entities = await fetch_all(model_entities_query)

    # outputs
    output_datasets_query = select(pipeline_output_dataset).where(
        pipeline_output_dataset.c.pipeline_id.in_(pipeline_ids))
    output_datasets = await fetch_all(output_datasets_query)

    output_model_entities_query = select(pipeline_output_model_entity).where(
        pipeline_output_model_entity.c.pipeline_id.in_(pipeline_ids))
    output_model_entities = await fetch_all(output_model_entities_query)

    # script
    implementation_scripts = await get_scripts(
        [p["implementation_script_id"] for p in pipeline_implementations])

    output_objs = []
    for pipe_id in pipeline_ids:
        pipe_record = next(
            iter([p for p in pipelines if p["id"] == pipe_id]), None)

        data_source_ids = [s["data_source_id"]
                           for s in data_sources if s["pipeline_id"] == pipe_id]
        dataset_ids = [s["dataset_id"]
                       for s in datasets if s["pipeline_id"] == pipe_id]
        model_entity_ids = [s["model_entity_id"]
                            for s in model_entities if s["pipeline_id"] == pipe_id]

        pipe_implementation_record = next(iter([
            p for p in pipeline_implementations if p["id"] == pipe_id]), None)

        pipeline_implementation_obj = None
        pipeline_outputs_obj = PipelineOutputEntities(
            dataset_ids=[], model_entity_ids=[])
        if pipe_implementation_record:
            runs_records = [
                r for r in pipeline_runs if r["pipeline_id"] == pipe_id]

            output_dataset_ids = [s["dataset_id"]
                                  for s in output_datasets if s["pipeline_id"] == pipe_id]
            output_model_entity_ids = [s["model_entity_id"]
                                       for s in output_model_entities if s["pipeline_id"] == pipe_id]

            function_ids_in_pipeline = [
                f["function_id"] for f in functions_in_pipelines if f["pipeline_id"] == pipe_id]
            functions_records = [
                f for f in function_records if f.id in function_ids_in_pipeline]

            implementation_script = next(
                iter([s for s in implementation_scripts if s.id == pipe_implementation_record["implementation_script_id"]]), None)

            pipeline_implementation_obj = PipelineImplementation(
                **pipe_implementation_record,
                functions=functions_records,
                runs=runs_records,
                implementation_script=implementation_script
            )

            pipeline_outputs_obj = PipelineOutputEntities(
                dataset_ids=output_dataset_ids,
                model_entity_ids=output_model_entity_ids
            )

        output_objs.append(Pipeline(
            **pipe_record,
            inputs=PipelineInputEntities(
                data_source_ids=data_source_ids,
                dataset_ids=dataset_ids,
                model_entity_ids=model_entity_ids
            ),
            outputs=pipeline_outputs_obj,
            implementation=pipeline_implementation_obj
        ))

    return output_objs


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
