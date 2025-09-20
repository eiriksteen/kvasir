import uuid
from datetime import datetime, timezone
from typing import List
from fastapi import HTTPException
from sqlalchemy import select, insert

from synesis_api.database.service import fetch_all, execute, fetch_one
from synesis_api.modules.pipeline.models import pipeline, function_in_pipeline, pipeline_periodic_schedule
from synesis_api.modules.function.models import function, function_input_structure, function_output_structure, function_output_variable
from synesis_api.modules.project.service import get_pipeline_ids_in_project
from synesis_schemas.main_server import (
    PipelineInDB,
    FunctionInPipelineInDB,
    FunctionBare,
    PipelineFull,
    PeriodicScheduleInDB,
    PipelineCreate,
)


async def create_pipeline(
    user_id: uuid.UUID,
    pipeline_create: PipelineCreate,
) -> PipelineInDB:

    pipeline_obj = PipelineInDB(
        id=uuid.uuid4(),
        user_id=user_id,
        name=pipeline_create.name,
        description=pipeline_create.description,
        created_at=datetime.now(timezone.utc),
        updated_at=datetime.now(timezone.utc)
    )

    await execute(insert(pipeline).values(**pipeline_obj.model_dump()), commit_after=True)

    if len(pipeline_create.periodic_schedules) > 0:

        periodic_schedule_records = [
            PeriodicScheduleInDB(
                id=uuid.uuid4(),
                pipeline_id=pipeline_obj.id,
                start_time=periodic_schedule.start_time if periodic_schedule.start_time else datetime.now(
                    timezone.utc),
                end_time=periodic_schedule.end_time,
                schedule_description=periodic_schedule.schedule_description,
                cron_expression=periodic_schedule.cron_expression,
                created_at=datetime.now(timezone.utc),
                updated_at=datetime.now(timezone.utc)
            ).model_dump() for periodic_schedule in pipeline_create.periodic_schedules
        ]

        await execute(insert(pipeline_periodic_schedule).values(periodic_schedule_records), commit_after=True)

    # TODO: Add on-event schedules

    fn_in_pipeline_records = []

    for i, function in enumerate(pipeline_create.functions):
        function_in_pipeline_obj = FunctionInPipelineInDB(
            id=uuid.uuid4(),
            pipeline_id=pipeline_obj.id,
            function_id=function.function_id,
            position=i,
            config=function.config,
            created_at=datetime.now(timezone.utc),
            updated_at=datetime.now(timezone.utc)
        )
        fn_in_pipeline_records.append(function_in_pipeline_obj.model_dump())

    await execute(insert(function_in_pipeline).values(fn_in_pipeline_records), commit_after=True)

    return pipeline_obj


async def get_user_pipelines_by_ids(user_id: uuid.UUID, pipeline_ids: List[uuid.UUID]) -> List[PipelineInDB]:
    pipelines = await fetch_all(
        select(pipeline).where(
            pipeline.c.user_id == user_id,
            pipeline.c.id.in_(pipeline_ids)
        )
    )
    return [PipelineInDB(**p) for p in pipelines]


async def get_project_pipelines(user_id: uuid.UUID, project_id: uuid.UUID) -> List[PipelineInDB]:
    pipeline_ids = await get_pipeline_ids_in_project(project_id)
    pipelines = await get_user_pipelines_by_ids(user_id, pipeline_ids)
    return pipelines


async def get_user_pipeline_with_functions(user_id: uuid.UUID, pipeline_id: uuid.UUID) -> PipelineFull:
    pipeline_record = await fetch_one(
        select(pipeline).where(
            pipeline.c.id == pipeline_id,
            pipeline.c.user_id == user_id
        )
    )

    function_records = await fetch_all(
        select(function).join(
            function_in_pipeline, function.c.id == function_in_pipeline.c.function_id
        ).where(
            function_in_pipeline.c.pipeline_id == pipeline_id
        ).order_by(
            function_in_pipeline.c.position
        )
    )

    if pipeline_record is None:
        raise HTTPException(status_code=404, detail="Pipeline not found")

    function_input_structures_records = await fetch_all(
        select(function_input_structure).where(
            function_input_structure.c.function_id.in_(
                [f["id"] for f in function_records])
        )
    )

    function_output_structures_records = await fetch_all(
        select(function_output_structure).where(
            function_output_structure.c.function_id.in_(
                [f["id"] for f in function_records])
        )
    )

    function_output_variables_records = await fetch_all(
        select(function_output_variable).where(
            function_output_variable.c.function_id.in_(
                [f["id"] for f in function_records])
        )
    )

    functions_with_inputs_and_outputs = []

    for fn in function_records:
        fn_inputs = [
            fi for fi in function_input_structures_records if fi["function_id"] == fn["id"]]
        fn_outputs = [
            fo for fo in function_output_structures_records if fo["function_id"] == fn["id"]]
        fn_output_variables = [
            fo for fo in function_output_variables_records if fo["function_id"] == fn["id"]]
        functions_with_inputs_and_outputs.append(
            FunctionBare(**fn, input_structures=fn_inputs, output_structures=fn_outputs, output_variables=fn_output_variables))

    return PipelineFull(
        **pipeline_record,
        functions=functions_with_inputs_and_outputs
    )
