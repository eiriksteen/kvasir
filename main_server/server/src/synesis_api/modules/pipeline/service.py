import uuid
from datetime import datetime, timezone
from typing import List, Optional
from sqlalchemy import select, insert

from synesis_api.database.service import fetch_all, execute
from synesis_api.modules.pipeline.models import (
    pipeline,
    function_in_pipeline,
    pipeline_periodic_schedule,
    pipeline_on_event_schedule,
    pipeline_from_dataset,
    pipeline_from_model_entity,
    pipeline_run,
    pipeline_object_group_output_to_save,
    pipeline_variable_group_output_to_save,
    function_in_pipeline_object_group_mapping
)
from synesis_api.modules.function.service import get_functions
from synesis_schemas.main_server import (
    PipelineInDB,
    FunctionInPipelineInDB,
    PipelineFull,
    PeriodicScheduleInDB,
    PipelineCreate,
    PipelineSources,
    PipelineFromDatasetInDB,
    PipelineFromModelEntityInDB,
    PipelineObjectGroupOutputToSaveInDB,
    PipelineVariableGroupOutputToSaveInDB,
    FunctionInPipelineObjectGroupMappingInDB,
)
from synesis_api.modules.project.service import get_pipeline_ids_in_project


async def create_pipeline(
    user_id: uuid.UUID,
    pipeline_create: PipelineCreate,
) -> PipelineInDB:

    pipeline_obj = PipelineInDB(
        id=uuid.uuid4(),
        user_id=user_id,
        name=pipeline_create.name,
        description=pipeline_create.description,
        implementation_script_path=pipeline_create.implementation_script_path,
        args_dataclass_name=pipeline_create.args_dataclass_name,
        input_dataclass_name=pipeline_create.input_dataclass_name,
        output_dataclass_name=pipeline_create.output_dataclass_name,
        output_variables_dataclass_name=pipeline_create.output_variables_dataclass_name,
        args_dict=pipeline_create.args_dict,
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
    output_object_group_to_save_records = []
    output_variable_group_to_save_records = []
    input_variable_mapping_records = []

    for pipeline_function_create in pipeline_create.functions:
        function_in_pipeline_obj = FunctionInPipelineInDB(
            id=uuid.uuid4(),
            pipeline_id=pipeline_obj.id,
            function_id=pipeline_function_create.function_id,
            created_at=datetime.now(timezone.utc),
            updated_at=datetime.now(timezone.utc)
        )
        fn_in_pipeline_records.append(function_in_pipeline_obj.model_dump())

        for output_object_group_to_save_id in pipeline_function_create.output_object_groups_to_save_ids:
            pipeline_object_group_output_to_save_obj = PipelineObjectGroupOutputToSaveInDB(
                id=uuid.uuid4(),
                pipeline_id=pipeline_obj.id,
                object_group_desc_id=output_object_group_to_save_id,
                created_at=datetime.now(timezone.utc),
                updated_at=datetime.now(timezone.utc)
            )
            output_object_group_to_save_records.append(
                pipeline_object_group_output_to_save_obj.model_dump())

        for output_variable_group_to_save_id in pipeline_function_create.output_variable_groups_to_save_ids:
            pipeline_variable_group_output_to_save_obj = PipelineVariableGroupOutputToSaveInDB(
                id=uuid.uuid4(),
                pipeline_id=pipeline_obj.id,
                variable_group_desc_id=output_variable_group_to_save_id,
                created_at=datetime.now(timezone.utc),
                updated_at=datetime.now(timezone.utc)
            )
            output_variable_group_to_save_records.append(
                pipeline_variable_group_output_to_save_obj.model_dump())

        for input_variable_mapping in pipeline_function_create.input_variable_mappings:
            pipeline_input_variable_mapping_obj = FunctionInPipelineObjectGroupMappingInDB(
                id=uuid.uuid4(),
                pipeline_id=pipeline_obj.id,
                from_function_output_object_group_id=input_variable_mapping.from_function_output_object_group_id,
                from_dataset_object_group_id=input_variable_mapping.from_dataset_object_group_id,
                to_function_input_object_group_id=input_variable_mapping.to_function_input_object_group_id,
                created_at=datetime.now(timezone.utc),
                updated_at=datetime.now(timezone.utc)
            )
            input_variable_mapping_records.append(
                pipeline_input_variable_mapping_obj.model_dump())

    if len(fn_in_pipeline_records) > 0:
        await execute(insert(function_in_pipeline).values(fn_in_pipeline_records), commit_after=True)
    if len(output_object_group_to_save_records) > 0:
        await execute(insert(pipeline_object_group_output_to_save).values(output_object_group_to_save_records), commit_after=True)
    if len(output_variable_group_to_save_records) > 0:
        await execute(insert(pipeline_variable_group_output_to_save).values(output_variable_group_to_save_records), commit_after=True)
    if len(input_variable_mapping_records) > 0:
        await execute(insert(function_in_pipeline_object_group_mapping).values(input_variable_mapping_records), commit_after=True)

    pipeline_from_dataset_records = [PipelineFromDatasetInDB(
        pipeline_id=pipeline_obj.id,
        dataset_id=dataset_id,
        created_at=datetime.now(timezone.utc),
        updated_at=datetime.now(timezone.utc)
    ).model_dump() for dataset_id in pipeline_create.input_dataset_ids]

    if len(pipeline_from_dataset_records) > 0:
        await execute(insert(pipeline_from_dataset).values(pipeline_from_dataset_records), commit_after=True)

    pipeline_from_model_records = [PipelineFromModelEntityInDB(
        pipeline_id=pipeline_obj.id,
        model_entity_id=model_entity_id,
        created_at=datetime.now(timezone.utc),
        updated_at=datetime.now(timezone.utc)
    ).model_dump() for model_entity_id in pipeline_create.input_model_entity_ids]

    if len(pipeline_from_model_records) > 0:
        await execute(insert(pipeline_from_model_entity).values(pipeline_from_model_records), commit_after=True)

    return pipeline_obj


async def get_user_pipelines(
    user_id: uuid.UUID,
    pipeline_ids: Optional[List[uuid.UUID]] = None,
    project_id: Optional[uuid.UUID] = None
):

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

    # sources
    dataset_sources_query = select(pipeline_from_dataset).where(
        pipeline_from_dataset.c.pipeline_id.in_(pipeline_ids))
    model_sources_query = select(pipeline_from_model_entity).where(
        pipeline_from_model_entity.c.pipeline_id.in_(pipeline_ids))

    dataset_sources = await fetch_all(dataset_sources_query)
    model_sources = await fetch_all(model_sources_query)

    output_objs = []
    for pipe_id in pipeline_ids:
        pipe_record = next(p for p in pipelines if p["id"] == pipe_id)
        runs_records = [
            r for r in pipeline_runs if r["pipeline_id"] == pipe_id]
        periodic_schedules_records = [
            s for s in periodic_schedules if s["pipeline_id"] == pipe_id]
        on_event_schedules_records = [
            s for s in on_event_schedules if s["pipeline_id"] == pipe_id]
        dataset_sources_records = [
            s for s in dataset_sources if s["pipeline_id"] == pipe_id]
        model_sources_records = [
            s for s in model_sources if s["pipeline_id"] == pipe_id]

        function_ids_in_pipeline = [
            f["function_id"] for f in functions_in_pipelines if f["pipeline_id"] == pipe_id]
        functions_records = [
            f for f in function_records if f.id in function_ids_in_pipeline]

        output_objs.append(PipelineFull(
            **pipe_record,
            functions=functions_records,
            runs=runs_records,
            periodic_schedules=periodic_schedules_records,
            on_event_schedules=on_event_schedules_records,
            sources=PipelineSources(
                dataset_ids=[s["dataset_id"] for s in dataset_sources_records],
                model_entity_ids=[s["model_entity_id"]
                                  for s in model_sources_records]
            )
        ))
    return output_objs


async def get_user_pipelines_by_ids(user_id: uuid.UUID, pipeline_ids: List[uuid.UUID]) -> List[PipelineFull]:
    return await get_user_pipelines(user_id, pipeline_ids=pipeline_ids)


async def get_project_pipelines(user_id: uuid.UUID, project_id: uuid.UUID) -> List[PipelineFull]:
    return await get_user_pipelines(user_id, project_id=project_id)
