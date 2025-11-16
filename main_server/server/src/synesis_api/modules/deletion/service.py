import uuid
from sqlalchemy import select, delete, update, and_
from fastapi import HTTPException

from synesis_api.database.service import execute, fetch_all, fetch_one
from synesis_api.modules.data_sources.models import (
    data_source,
    file_data_source,
)
from synesis_api.modules.data_sources.service import get_user_data_sources
from synesis_api.modules.data_objects.models import (
    dataset,
    object_group,
    data_object,
    time_series_group,
    time_series,
    tabular_group,
    tabular,
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
    function_in_pipeline,
    pipeline_run,
)
from synesis_api.modules.entity_graph.models import (
    dataset_from_data_source,
    data_source_supported_in_pipeline,
    dataset_supported_in_pipeline,
    model_entity_supported_in_pipeline,
    dataset_in_pipeline_run,
    data_source_in_pipeline_run,
    model_entity_in_pipeline_run,
    pipeline_run_output_dataset,
    pipeline_run_output_model_entity,
    pipeline_run_output_data_source,
    data_source_in_analysis,
    dataset_in_analysis,
    model_entity_in_analysis,
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
    analysis_in_run,
    analysis_from_run,
)
from synesis_api.modules.orchestrator.models import (
    data_source_context,
    dataset_context,
    model_entity_context,
    pipeline_context,
    analysis_context,
)
from synesis_api.modules.analysis.models import (
    analysis,
    notebook,
    notebook_section,
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
        delete(dataset_from_data_source).where(
            dataset_from_data_source.c.data_source_id == data_source_id
        ),
        commit_after=True
    )

    await execute(
        delete(data_source_supported_in_pipeline).where(
            data_source_supported_in_pipeline.c.data_source_id == data_source_id
        ),
        commit_after=True
    )

    await execute(
        delete(data_source_in_pipeline_run).where(
            data_source_in_pipeline_run.c.data_source_id == data_source_id
        ),
        commit_after=True
    )

    await execute(
        delete(pipeline_run_output_data_source).where(
            pipeline_run_output_data_source.c.data_source_id == data_source_id
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
                delete(tabular).where(
                    tabular.c.id.in_(data_object_ids)),
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
            delete(tabular_group).where(
                tabular_group.c.id.in_(object_group_ids)
            ),
            commit_after=True
        )

        await execute(
            delete(object_group).where(
                object_group.c.id.in_(object_group_ids)),
            commit_after=True
        )

    await execute(
        delete(dataset_from_data_source).where(
            dataset_from_data_source.c.dataset_id == dataset_id
        ),
        commit_after=True
    )

    await execute(
        delete(dataset_supported_in_pipeline).where(
            dataset_supported_in_pipeline.c.dataset_id == dataset_id
        ),
        commit_after=True
    )

    await execute(
        delete(dataset_in_pipeline_run).where(
            dataset_in_pipeline_run.c.dataset_id == dataset_id
        ),
        commit_after=True
    )

    await execute(
        delete(pipeline_run_output_dataset).where(
            pipeline_run_output_dataset.c.dataset_id == dataset_id
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
        delete(model_entity_supported_in_pipeline).where(
            model_entity_supported_in_pipeline.c.model_entity_id == model_entity_id
        ),
        commit_after=True
    )

    await execute(
        delete(model_entity_in_pipeline_run).where(
            model_entity_in_pipeline_run.c.model_entity_id == model_entity_id
        ),
        commit_after=True
    )

    await execute(
        delete(pipeline_run_output_model_entity).where(
            pipeline_run_output_model_entity.c.model_entity_id == model_entity_id
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

    # Get all pipeline runs to delete their associations
    pipeline_runs_query = select(pipeline_run).where(
        pipeline_run.c.pipeline_id == pipeline_id)
    pipeline_runs_result = await fetch_all(pipeline_runs_query)
    pipeline_run_ids = [pr["id"] for pr in pipeline_runs_result]

    if pipeline_run_ids:
        # Delete pipeline run input associations
        await execute(
            delete(dataset_in_pipeline_run).where(
                dataset_in_pipeline_run.c.pipeline_run_id.in_(pipeline_run_ids)
            ),
            commit_after=True
        )

        await execute(
            delete(data_source_in_pipeline_run).where(
                data_source_in_pipeline_run.c.pipeline_run_id.in_(
                    pipeline_run_ids)
            ),
            commit_after=True
        )

        await execute(
            delete(model_entity_in_pipeline_run).where(
                model_entity_in_pipeline_run.c.pipeline_run_id.in_(
                    pipeline_run_ids)
            ),
            commit_after=True
        )

        # Delete pipeline run output associations
        await execute(
            delete(pipeline_run_output_dataset).where(
                pipeline_run_output_dataset.c.pipeline_run_id.in_(
                    pipeline_run_ids)
            ),
            commit_after=True
        )

        await execute(
            delete(pipeline_run_output_model_entity).where(
                pipeline_run_output_model_entity.c.pipeline_run_id.in_(
                    pipeline_run_ids)
            ),
            commit_after=True
        )

        await execute(
            delete(pipeline_run_output_data_source).where(
                pipeline_run_output_data_source.c.pipeline_run_id.in_(
                    pipeline_run_ids)
            ),
            commit_after=True
        )

    # Delete pipeline runs
    await execute(
        delete(pipeline_run).where(pipeline_run.c.pipeline_id == pipeline_id),
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
        delete(function_in_pipeline).where(
            function_in_pipeline.c.pipeline_id == pipeline_id
        ),
        commit_after=True
    )

    await execute(
        delete(data_source_supported_in_pipeline).where(
            data_source_supported_in_pipeline.c.pipeline_id == pipeline_id
        ),
        commit_after=True
    )

    await execute(
        delete(dataset_supported_in_pipeline).where(
            dataset_supported_in_pipeline.c.pipeline_id == pipeline_id
        ),
        commit_after=True
    )

    await execute(
        delete(model_entity_supported_in_pipeline).where(
            model_entity_supported_in_pipeline.c.pipeline_id == pipeline_id
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
        update(model_entity_implementation).where(
            model_entity_implementation.c.pipeline_id == pipeline_id
        ).values(pipeline_id=None),
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


async def delete_notebook_section_recursive(section_id: uuid.UUID) -> None:
    """Recursively delete a notebook section and all its children."""
    # Import here to avoid circular dependency
    from synesis_api.modules.analysis.service.service_notebook import delete_notebook_section_recursive as delete_section
    await delete_section(section_id)


async def delete_analysis(user_id: uuid.UUID, analysis_id: uuid.UUID) -> uuid.UUID:
    """Delete an analysis and all its associated data."""
    # Verify the analysis exists and user owns it
    analysis_query = select(analysis).where(
        and_(
            analysis.c.id == analysis_id,
            analysis.c.user_id == user_id
        )
    )
    analysis_result = await fetch_one(analysis_query)
    if not analysis_result:
        raise HTTPException(status_code=404, detail="Analysis not found")

    notebook_id = analysis_result["notebook_id"]

    # Get all top-level sections of the notebook
    sections_to_delete = await fetch_all(
        select(notebook_section).where(
            notebook_section.c.notebook_id == notebook_id,
            notebook_section.c.parent_section_id == None
        )
    )

    section_ids = [section["id"] for section in sections_to_delete]

    # Delete all sections recursively
    for section_id in section_ids:
        await delete_notebook_section_recursive(section_id)

    # Delete run associations
    await execute(
        delete(analysis_in_run).where(
            analysis_in_run.c.analysis_id == analysis_id
        ),
        commit_after=True
    )

    await execute(
        delete(analysis_from_run).where(
            analysis_from_run.c.analysis_id == analysis_id
        ),
        commit_after=True
    )

    # Delete entity graph associations
    await execute(
        delete(data_source_in_analysis).where(
            data_source_in_analysis.c.analysis_id == analysis_id
        ),
        commit_after=True
    )

    await execute(
        delete(dataset_in_analysis).where(
            dataset_in_analysis.c.analysis_id == analysis_id
        ),
        commit_after=True
    )

    await execute(
        delete(model_entity_in_analysis).where(
            model_entity_in_analysis.c.analysis_id == analysis_id
        ),
        commit_after=True
    )

    # Delete analysis context
    await execute(
        delete(analysis_context).where(
            analysis_context.c.analysis_id == analysis_id
        ),
        commit_after=True
    )

    # Delete the notebook
    await execute(
        delete(notebook).where(notebook.c.id == notebook_id),
        commit_after=True
    )

    # Delete the analysis itself
    await execute(
        delete(analysis).where(
            and_(
                analysis.c.id == analysis_id,
                analysis.c.user_id == user_id
            )
        ),
        commit_after=True
    )

    return analysis_id
