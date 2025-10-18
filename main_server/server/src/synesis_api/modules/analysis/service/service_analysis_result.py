import uuid
from sqlalchemy import update, select, insert, delete
from typing import List


from synesis_api.database.service import execute, fetch_one, fetch_all
from synesis_api.modules.analysis.models import (
    analysis_object, 
    analysis_result, 
    analysis_result_dataset,
    notebook_section,
    analysis_result_data_source,
)
from synesis_api.modules.data_objects.models import aggregation_object
from synesis_api.modules.analysis.models import plot
from synesis_api.modules.analysis.models import table
from synesis_schemas.main_server import (
    AnalysisResult,
    AnalysisResultInDB,
    AnalysisResultUpdate
)
from synesis_api.modules.analysis.service.service_utils import (
    get_last_element_in_section,
    get_prev_element,
)

async def create_analysis_result(analysis_result_arg: AnalysisResult) -> AnalysisResultInDB:
    last_type, last_id = await get_last_element_in_section(analysis_result_arg.section_id)
    if last_type == "analysis_result":
        await execute(
            update(analysis_result).where(analysis_result.c.id == last_id).values(
                next_type="analysis_result",
                next_id=analysis_result_arg.id
            ),
            commit_after=True
        )
    elif last_type == "notebook_section":
        await execute(
            update(notebook_section).where(notebook_section.c.id == last_id).values(
                next_type="analysis_result",
                next_id=analysis_result_arg.id
            ),
            commit_after=True
        )
    analysis_result_in_db = AnalysisResultInDB(
        **analysis_result_arg.model_dump()
    )

    await execute(
        insert(analysis_result).values(
            **analysis_result_in_db.model_dump()
        ),
        commit_after=True
    )

    # Add dataset mappings
    if analysis_result_arg.dataset_ids:
        for dataset_id in analysis_result_arg.dataset_ids:
            await execute(
                insert(analysis_result_dataset).values(
                    analysis_result_id=analysis_result_in_db.id,
                    dataset_id=dataset_id
                ),
                commit_after=True
            )
    
    # Add datasource mappings
    if analysis_result_arg.data_source_ids:
        for data_source_id in analysis_result_arg.data_source_ids:
            await execute(
                insert(analysis_result_data_source).values(
                    analysis_result_id=analysis_result_in_db.id,
                    data_source_id=data_source_id
                ),
                commit_after=True
            )

    return analysis_result_in_db



async def add_analysis_result_to_section(section_id: uuid.UUID, analysis_result_id: uuid.UUID) -> None:
    prev_type, prev_id = await get_last_element_in_section(section_id)

    if prev_type == "analysis_result":
        await execute(
            update(analysis_result).where(analysis_result.c.id == prev_id).values(
                next_type="analysis_result",
                next_id=analysis_result_id
            ),
            commit_after=True
        )
    elif prev_type == "notebook_section":
        await execute(
            update(notebook_section).where(notebook_section.c.id == prev_id).values(
                next_type="analysis_result",
                next_id=analysis_result_id
            ),
            commit_after=True
        )

    await execute(
        update(analysis_result).where(analysis_result.c.id == analysis_result_id).values(
            section_id=section_id
        ),
        commit_after=True
    )


async def get_data_source_ids_by_analysis_result_id(analysis_result_id: uuid.UUID) -> List[uuid.UUID]:
    data_source_mappings = await fetch_all(
        select(analysis_result_data_source).where(analysis_result_data_source.c.analysis_result_id == analysis_result_id)
    )
    return [mapping["data_source_id"] for mapping in data_source_mappings]


async def get_dataset_ids_by_analysis_result_id(analysis_result_id: uuid.UUID) -> List[uuid.UUID]:
    dataset_mappings = await fetch_all(
        select(analysis_result_dataset).where(analysis_result_dataset.c.analysis_result_id == analysis_result_id)
    )
    
    return [mapping["dataset_id"] for mapping in dataset_mappings]


async def check_user_owns_analysis_object(user_id: uuid.UUID, analysis_object_id: uuid.UUID) -> bool:
    result = await fetch_one(
        select(analysis_object).where(
            analysis_object.c.id == analysis_object_id,
            analysis_object.c.user_id == user_id
        )
    )
    return result is not None



async def delete_analysis_result(analysis_result_id: uuid.UUID) -> None:
    current_analysis_result = await get_analysis_result_by_id(analysis_result_id)
    previous_type, previous_id = await get_prev_element(analysis_result_id, "analysis_result", current_analysis_result.section_id)
    if previous_type == "analysis_result":
        await execute(
            update(analysis_result).where(analysis_result.c.id == previous_id).values(
                next_type=current_analysis_result.next_type,
                next_id=current_analysis_result.next_id,
            ),
            commit_after=True
        )
    elif previous_type == "notebook_section":
        await execute(
            update(notebook_section).where(notebook_section.c.id == previous_id).values(
                next_type=current_analysis_result.next_type,
                next_id=current_analysis_result.next_id,
            ),
            commit_after=True
        )
    await execute(
        delete(analysis_result_dataset).where(analysis_result_dataset.c.analysis_result_id == analysis_result_id),
        commit_after=True
    )
    await execute(
        delete(analysis_result_data_source).where(analysis_result_data_source.c.analysis_result_id == analysis_result_id),
        commit_after=True
    )
    await execute(
        delete(plot).where(plot.c.analysis_result_id == analysis_result_id),
        commit_after=True
    )
    await execute(
        delete(table).where(table.c.analysis_result_id == analysis_result_id),
        commit_after=True
    )
    await execute(
        delete(aggregation_object).where(aggregation_object.c.analysis_result_id == analysis_result_id),
        commit_after=True
    )
    
    await execute(
        delete(analysis_result).where(analysis_result.c.id == analysis_result_id),
        commit_after=True
    )


async def get_analysis_result_by_id(analysis_result_id: uuid.UUID) -> AnalysisResult:
    result = await fetch_one(
        select(analysis_result).where(analysis_result.c.id == analysis_result_id)
    )

    if result is None:
        return None

    dataset_ids = await get_dataset_ids_by_analysis_result_id(result["id"])
    data_source_ids = await get_data_source_ids_by_analysis_result_id(result["id"])

    return AnalysisResult(**result, dataset_ids=dataset_ids, data_source_ids=data_source_ids)

async def get_analysis_results_by_section_id(section_id: uuid.UUID) -> List[AnalysisResult]:
    """Get all analysis results for a given section_id"""
    # Get analysis result IDs from the mapping table
    results = await fetch_all(
        select(analysis_result).where(
            analysis_result.c.section_id == section_id
        )
    )
    
    
    analysis_results_list = []
    for result in results:
        dataset_ids = await get_dataset_ids_by_analysis_result_id(result["id"])
        data_source_ids = await get_data_source_ids_by_analysis_result_id(result["id"])
        analysis_results_list.append(AnalysisResult(**result, dataset_ids=dataset_ids, data_source_ids=data_source_ids))
    
    return analysis_results_list


async def get_analysis_results_by_ids(analysis_result_ids: List[uuid.UUID]) -> List[AnalysisResult]:
    results = await fetch_all(
        select(analysis_result).where(analysis_result.c.id.in_(analysis_result_ids))
    )

    analysis_results_list = []
    for result in results:
        dataset_ids = await get_dataset_ids_by_analysis_result_id(result["id"])
        analysis_results_list.append(AnalysisResult(**result, dataset_ids=dataset_ids))
    return analysis_results_list


async def update_analysis_result(analysis_result_arg: AnalysisResult) -> AnalysisResult:
    update_data = AnalysisResultInDB(**analysis_result_arg.model_dump())
    
    await execute(
        update(analysis_result).where(analysis_result.c.id == analysis_result_arg.id).values(
            **update_data.model_dump()
        ),
        commit_after=True
    )
    
    # Handle dataset_ids separately since they're stored in a junction table
    if analysis_result_arg.dataset_ids is not None:
        # First, remove existing dataset mappings
        await execute(
            delete(analysis_result_dataset).where(
                analysis_result_dataset.c.analysis_result_id == analysis_result_arg.id
            ),
            commit_after=True
        )
        
        # Then add new dataset mappings
        if analysis_result_arg.dataset_ids:
            for dataset_id in analysis_result_arg.dataset_ids:
                await execute(
                    insert(analysis_result_dataset).values(
                        analysis_result_id=analysis_result_arg.id,
                        dataset_id=dataset_id
                    ),
                    commit_after=True
                )
    if analysis_result_arg.data_source_ids is not None:
        await execute(
            delete(analysis_result_data_source).where(
                analysis_result_data_source.c.analysis_result_id == analysis_result_arg.id
            ),
            commit_after=True
        )
        if analysis_result_arg.data_source_ids:
            for data_source_id in analysis_result_arg.data_source_ids:
                await execute(
                    insert(analysis_result_data_source).values(
                        analysis_result_id=analysis_result_arg.id,
                        data_source_id=data_source_id
                    ),
                    commit_after=True
                )
    
    return analysis_result



async def update_analysis_result_by_id(analysis_result_id: uuid.UUID, analysis_result_update: AnalysisResultUpdate) -> AnalysisResultInDB:
    await execute(
        update(analysis_result).where(analysis_result.c.id == analysis_result_id).values(
            **analysis_result_update.model_dump()
        ),
        commit_after=True
    )
    result = await get_analysis_result_by_id(analysis_result_id)
    return result
