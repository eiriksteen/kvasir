import uuid
from sqlalchemy import select, delete, and_
from fastapi import HTTPException

from synesis_api.database.service import execute, fetch_all
from synesis_api.modules.data_sources.models import (
    data_source,
    file_data_source,
    data_source_from_pipeline,
)
from synesis_api.modules.data_sources.service import get_user_data_sources
from synesis_api.modules.data_objects.models import (
    dataset,
    object_group,
    data_object,
    time_series_group,
    time_series,
    object_group_from_pipeline,
    object_group_from_data_source,
)
from synesis_api.modules.data_objects.service import get_user_datasets
from synesis_api.modules.model.models import (
    model_entity,
    model_entity_implementation,
)
from synesis_api.modules.model.service import get_user_model_entities
from synesis_api.modules.pipeline.models import (
    pipeline,
    pipeline_implementation,
    data_source_in_pipeline,
    dataset_in_pipeline,
    model_entity_in_pipeline,
    analysis_in_pipeline,
    function_in_pipeline,
    pipeline_run,
    pipeline_output_dataset,
    pipeline_output_model_entity,
)
from synesis_api.modules.pipeline.service import get_user_pipelines
from synesis_api.modules.runs.models import (
    pipeline_from_run,
    pipeline_in_run,
    data_source_in_run,
    data_source_from_run,
    dataset_in_run,
    dataset_from_run,
    model_entity_in_run,
    model_entity_from_run,
)
from synesis_api.modules.analysis.models import (
    data_source_in_analysis,
    dataset_in_analysis,
    model_entity_in_analysis,
)
from synesis_api.modules.orchestrator.models import (
    data_source_context,
    dataset_context,
    model_entity_context,
    pipeline_context,
)


async def delete_data_source(user_id: uuid.UUID, data_source_id: uuid.UUID) -> uuid.UUID:
    data_sources = await get_user_data_sources(user_id, [data_source_id])
    if not data_sources:
        raise HTTPException(status_code=404, detail="Data source not found")

    await execute(
        delete(file_data_source).where(
            file_data_source.c.id == data_source_id),
        commit_after=True
    )

    await execute(
        delete(data_source_from_pipeline).where(
            data_source_from_pipeline.c.data_source_id == data_source_id
        ),
        commit_after=True
    )

    await execute(
        delete(object_group_from_data_source).where(
            object_group_from_data_source.c.data_source_id == data_source_id
        ),
        commit_after=True
    )

    await execute(
        delete(data_source_in_pipeline).where(
            data_source_in_pipeline.c.data_source_id == data_source_id
        ),
        commit_after=True
    )

    await execute(
        delete(data_source_in_run).where(
            data_source_in_run.c.data_source_id == data_source_id
        ),
        commit_after=True
    )

    await execute(
        delete(data_source_from_run).where(
            data_source_from_run.c.data_source_id == data_source_id
        ),
        commit_after=True
    )

    await execute(
        delete(data_source_in_analysis).where(
            data_source_in_analysis.c.data_source_id == data_source_id
        ),
        commit_after=True
    )

    await execute(
        delete(data_source_context).where(
            data_source_context.c.data_source_id == data_source_id
        ),
        commit_after=True
    )

    await execute(
        delete(data_source).where(
            and_(
                data_source.c.id == data_source_id,
                data_source.c.user_id == user_id
            )
        ),
        commit_after=True
    )

    return data_source_id


async def delete_dataset(user_id: uuid.UUID, dataset_id: uuid.UUID) -> uuid.UUID:
    datasets = await get_user_datasets(user_id, [dataset_id])
    if not datasets:
        raise HTTPException(status_code=404, detail="Dataset not found")

    object_groups_query = select(object_group).where(
        object_group.c.dataset_id == dataset_id
    )
    object_groups_result = await fetch_all(object_groups_query)
    object_group_ids = [og["id"] for og in object_groups_result]

    if object_group_ids:
        data_objects_query = select(data_object).where(
            data_object.c.group_id.in_(object_group_ids)
        )
        data_objects_result = await fetch_all(data_objects_query)
        data_object_ids = [do["id"] for do in data_objects_result]

        if data_object_ids:
            await execute(
                delete(time_series).where(
                    time_series.c.id.in_(data_object_ids)),
                commit_after=True
            )

            await execute(
                delete(data_object).where(
                    data_object.c.id.in_(data_object_ids)),
                commit_after=True
            )

        await execute(
            delete(time_series_group).where(
                time_series_group.c.id.in_(object_group_ids)
            ),
            commit_after=True
        )

        await execute(
            delete(object_group_from_pipeline).where(
                object_group_from_pipeline.c.object_group_id.in_(
                    object_group_ids)
            ),
            commit_after=True
        )

        await execute(
            delete(object_group_from_data_source).where(
                object_group_from_data_source.c.object_group_id.in_(
                    object_group_ids)
            ),
            commit_after=True
        )

        await execute(
            delete(object_group).where(
                object_group.c.id.in_(object_group_ids)),
            commit_after=True
        )

    await execute(
        delete(dataset_in_pipeline).where(
            dataset_in_pipeline.c.dataset_id == dataset_id
        ),
        commit_after=True
    )

    await execute(
        delete(pipeline_output_dataset).where(
            pipeline_output_dataset.c.dataset_id == dataset_id
        ),
        commit_after=True
    )

    await execute(
        delete(dataset_in_run).where(
            dataset_in_run.c.dataset_id == dataset_id
        ),
        commit_after=True
    )

    await execute(
        delete(dataset_from_run).where(
            dataset_from_run.c.dataset_id == dataset_id
        ),
        commit_after=True
    )

    await execute(
        delete(dataset_in_analysis).where(
            dataset_in_analysis.c.dataset_id == dataset_id
        ),
        commit_after=True
    )

    await execute(
        delete(dataset_context).where(
            dataset_context.c.dataset_id == dataset_id
        ),
        commit_after=True
    )

    await execute(
        delete(dataset).where(
            and_(
                dataset.c.id == dataset_id,
                dataset.c.user_id == user_id
            )
        ),
        commit_after=True
    )

    return dataset_id


async def delete_model_entity(user_id: uuid.UUID, model_entity_id: uuid.UUID) -> uuid.UUID:
    model_entities = await get_user_model_entities(user_id, [model_entity_id])
    if not model_entities:
        raise HTTPException(status_code=404, detail="Model entity not found")

    await execute(
        delete(model_entity_implementation).where(
            model_entity_implementation.c.id == model_entity_id
        ),
        commit_after=True
    )

    await execute(
        delete(model_entity_in_pipeline).where(
            model_entity_in_pipeline.c.model_entity_id == model_entity_id
        ),
        commit_after=True
    )

    await execute(
        delete(pipeline_output_model_entity).where(
            pipeline_output_model_entity.c.model_entity_id == model_entity_id
        ),
        commit_after=True
    )

    await execute(
        delete(model_entity_in_run).where(
            model_entity_in_run.c.model_entity_id == model_entity_id
        ),
        commit_after=True
    )

    await execute(
        delete(model_entity_from_run).where(
            model_entity_from_run.c.model_entity_id == model_entity_id
        ),
        commit_after=True
    )

    await execute(
        delete(model_entity_in_analysis).where(
            model_entity_in_analysis.c.model_entity_id == model_entity_id
        ),
        commit_after=True
    )

    await execute(
        delete(model_entity_context).where(
            model_entity_context.c.model_entity_id == model_entity_id
        ),
        commit_after=True
    )

    await execute(
        delete(model_entity).where(
            and_(
                model_entity.c.id == model_entity_id,
                model_entity.c.user_id == user_id
            )
        ),
        commit_after=True
    )

    return model_entity_id


async def delete_pipeline(user_id: uuid.UUID, pipeline_id: uuid.UUID) -> uuid.UUID:
    pipelines = await get_user_pipelines(user_id, [pipeline_id])
    if not pipelines:
        raise HTTPException(status_code=404, detail="Pipeline not found")

    await execute(
        delete(pipeline_run).where(pipeline_run.c.pipeline_id == pipeline_id),
        commit_after=True
    )

    await execute(
        delete(function_in_pipeline).where(
            function_in_pipeline.c.pipeline_id == pipeline_id
        ),
        commit_after=True
    )

    await execute(
        delete(data_source_in_pipeline).where(
            data_source_in_pipeline.c.pipeline_id == pipeline_id
        ),
        commit_after=True
    )

    await execute(
        delete(dataset_in_pipeline).where(
            dataset_in_pipeline.c.pipeline_id == pipeline_id
        ),
        commit_after=True
    )

    await execute(
        delete(model_entity_in_pipeline).where(
            model_entity_in_pipeline.c.pipeline_id == pipeline_id
        ),
        commit_after=True
    )

    await execute(
        delete(analysis_in_pipeline).where(
            analysis_in_pipeline.c.pipeline_id == pipeline_id
        ),
        commit_after=True
    )

    await execute(
        delete(pipeline_output_dataset).where(
            pipeline_output_dataset.c.pipeline_id == pipeline_id
        ),
        commit_after=True
    )

    await execute(
        delete(pipeline_output_model_entity).where(
            pipeline_output_model_entity.c.pipeline_id == pipeline_id
        ),
        commit_after=True
    )

    await execute(
        delete(data_source_from_pipeline).where(
            data_source_from_pipeline.c.pipeline_id == pipeline_id
        ),
        commit_after=True
    )

    await execute(
        delete(pipeline_from_run).where(
            pipeline_from_run.c.pipeline_id == pipeline_id
        ),
        commit_after=True
    )

    await execute(
        delete(pipeline_in_run).where(
            pipeline_in_run.c.pipeline_id == pipeline_id
        ),
        commit_after=True
    )

    await execute(
        delete(pipeline_context).where(
            pipeline_context.c.pipeline_id == pipeline_id
        ),
        commit_after=True
    )

    await execute(
        delete(pipeline_implementation).where(
            pipeline_implementation.c.id == pipeline_id
        ),
        commit_after=True
    )

    await execute(
        delete(pipeline).where(
            and_(
                pipeline.c.id == pipeline_id,
                pipeline.c.user_id == user_id
            )
        ),
        commit_after=True
    )

    return pipeline_id
