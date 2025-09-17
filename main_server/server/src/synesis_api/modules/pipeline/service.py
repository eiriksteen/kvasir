import uuid
from datetime import datetime, timezone
from typing import List, Optional
from fastapi import HTTPException
from sqlalchemy import select, insert, or_

from synesis_api.database.service import fetch_all, execute, fetch_one
from synesis_api.modules.pipeline.models import (
    function, function_input_structure, function_output_structure, function_output_variable, pipeline, function_in_pipeline, pipeline_periodic_schedule
)
from synesis_schemas.main_server import (
    PipelineInDB,
    FunctionInDB,
    FunctionInputStructureInDB,
    FunctionOutputStructureInDB,
    FunctionOutputVariableInDB,
    FunctionCreate,
    FunctionInPipelineInDB,
    FunctionBare,
    PipelineFull,
    PeriodicScheduleInDB,
    PipelineCreate
)
from synesis_api.utils.rag_utils import embed


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


async def get_user_pipelines(user_id: uuid.UUID) -> List[PipelineInDB]:
    pipelines = await fetch_all(
        select(pipeline).where(pipeline.c.user_id == user_id)
    )
    pipeline_objs = [PipelineInDB(**p) for p in pipelines]
    return pipeline_objs


async def create_function(function_create: FunctionCreate) -> FunctionInDB:

    embedding = (await embed([function_create.description]))[0]

    function_obj = FunctionInDB(
        id=uuid.uuid4(),
        name=function_create.name,
        description=function_create.description,
        type=function_create.type,
        implementation_script_path=str(
            function_create.implementation_script_path),
        setup_script_path=str(
            function_create.setup_script_path) if function_create.setup_script_path else None,
        config_dict=function_create.default_config,
        embedding=embedding,
        created_at=datetime.now(timezone.utc),
        updated_at=datetime.now(timezone.utc)
    )

    await execute(insert(function).values(**function_obj.model_dump()), commit_after=True)

    input_structure_records = [
        FunctionInputStructureInDB(
            id=uuid.uuid4(),
            function_id=function_obj.id,
            structure_id=input.structure_id,
            name=input.name,
            description=input.description,
            required=input.required,
            created_at=datetime.now(timezone.utc),
            updated_at=datetime.now(timezone.utc)
        ).model_dump() for input in function_create.input_structures
    ]

    if input_structure_records:
        await execute(insert(function_input_structure).values(input_structure_records), commit_after=True)

    output_structure_records = [
        FunctionOutputStructureInDB(
            id=uuid.uuid4(),
            function_id=function_obj.id,
            structure_id=output.structure_id,
            name=output.name,
            description=output.description,
            created_at=datetime.now(timezone.utc),
            updated_at=datetime.now(timezone.utc)
        ).model_dump() for output in function_create.output_structures
    ]

    if output_structure_records:
        await execute(insert(function_output_structure).values(output_structure_records), commit_after=True)

    output_variable_records = [
        FunctionOutputVariableInDB(
            id=uuid.uuid4(),
            function_id=function_obj.id,
            name=output.name,
            python_type=output.python_type,
            description=output.description,
            created_at=datetime.now(timezone.utc),
            updated_at=datetime.now(timezone.utc)
        ).model_dump() for output in function_create.output_variables
    ]

    if output_variable_records:
        await execute(insert(function_output_variable).values(output_variable_records), commit_after=True)

    return function_obj


async def check_function_ids_exist(function_ids: List[uuid.UUID]) -> bool:
    """Check if all function IDs exist"""

    query = select(function.c.id).where(function.c.id.in_(function_ids))
    results = await fetch_all(query)

    return len(results) == len(function_ids)


async def get_user_pipelines_by_ids(user_id: uuid.UUID, pipeline_ids: List[uuid.UUID]) -> List[PipelineInDB]:
    pipelines = await fetch_all(
        select(pipeline).where(
            pipeline.c.user_id == user_id,
            pipeline.c.id.in_(pipeline_ids)
        )
    )
    return [PipelineInDB(**p) for p in pipelines]


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
