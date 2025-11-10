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
    pipeline_run,
)
from synesis_api.modules.function.service import get_functions
from synesis_schemas.main_server import (
    PipelineInDB,
    PipelineImplementationInDB,
    Pipeline,
    PipelineImplementation,
    PipelineImplementationCreate,
    PipelineRunInDB,
    PipelineCreate,
    FunctionInPipelineInDB,
    PipelineRunCreate,
)


async def create_pipeline(user_id: uuid.UUID, pipeline_create: PipelineCreate) -> PipelineInDB:
    pipeline_record = PipelineInDB(
        id=uuid.uuid4(),
        user_id=user_id,
        **pipeline_create.model_dump(),
        created_at=datetime.now(timezone.utc),
        updated_at=datetime.now(timezone.utc)
    )

    await execute(insert(pipeline).values(pipeline_record.model_dump()), commit_after=True)

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

    if not pipelines:
        return []

    pipeline_ids = [p["id"] for p in pipelines]

    pipeline_implementation_query = select(pipeline_implementation).where(
        pipeline_implementation.c.id.in_(pipeline_ids))

    pipeline_implementations = await fetch_all(pipeline_implementation_query)

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

    output_objs = []
    for pipe_id in pipeline_ids:
        pipe_obj = PipelineInDB(**next(
            iter([p for p in pipelines if p["id"] == pipe_id])))

        pipe_implementation_record = next(iter([
            p for p in pipeline_implementations if p["id"] == pipe_id]), None)

        pipeline_implementation_obj = None
        if pipe_implementation_record:

            function_ids_in_pipeline = [
                f["function_id"] for f in functions_in_pipelines if f["pipeline_id"] == pipe_id]
            functions_records = [
                f for f in function_records if f.id in function_ids_in_pipeline]

            pipeline_implementation_obj = PipelineImplementation(
                **pipe_implementation_record,
                functions=functions_records
            )

        runs_objs = []
        runs_records = [
            r for r in pipeline_runs if r["pipeline_id"] == pipe_id]

        for run_record in runs_records:
            runs_objs.append(PipelineRunInDB(**run_record))

        output_objs.append(Pipeline(
            **pipe_obj.model_dump(),
            runs=runs_objs,
            implementation=pipeline_implementation_obj
        ))

    return output_objs


async def create_pipeline_run(pipeline_run_create: PipelineRunCreate) -> PipelineRunInDB:
    pipeline_run_obj = PipelineRunInDB(
        id=uuid.uuid4(),
        **pipeline_run_create.model_dump(),
        start_time=datetime.now(timezone.utc),
        created_at=datetime.now(timezone.utc),
        updated_at=datetime.now(timezone.utc))
    await execute(insert(pipeline_run).values(pipeline_run_obj.model_dump()), commit_after=True)

    # Input/output associations are now managed by project_graph module

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

    if not pipeline_runs:
        return []

    result = []
    for run in pipeline_runs:
        result.append(PipelineRunInDB(**run))

    return result


async def update_pipeline_run_status(pipeline_run_id: uuid.UUID, status: Literal["running", "completed", "failed"]) -> PipelineRunInDB:
    pipeline_run_obj = await fetch_one(select(pipeline_run).where(pipeline_run.c.id == pipeline_run_id))
    await execute(pipeline_run.update().where(pipeline_run.c.id == pipeline_run_id).values(status=status), commit_after=True)
    pipeline_run_obj["status"] = status
    return PipelineRunInDB(**pipeline_run_obj)
