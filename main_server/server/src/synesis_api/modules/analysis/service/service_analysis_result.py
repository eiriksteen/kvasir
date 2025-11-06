import uuid
from sqlalchemy import update, select, insert, delete
from typing import List


from synesis_api.database.service import execute, fetch_one, fetch_all
from synesis_api.modules.analysis.models import (
    analysis,
    analysis_result,
    notebook_section,
    result_image,
    result_chart,
    result_table,
)
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

    for image_url in analysis_result_arg.image_urls:
        await execute(
            insert(result_image).values(
                id=uuid.uuid4(),
                analysis_result_id=analysis_result_in_db.id,
                image_url=image_url
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


async def check_user_owns_analysis(user_id: uuid.UUID, analysis_id: uuid.UUID) -> bool:
    result = await fetch_one(
        select(analysis).where(
            analysis.c.id == analysis_id,
            analysis.c.user_id == user_id
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
        delete(result_image).where(
            result_image.c.analysis_result_id == analysis_result_id),
        commit_after=True
    )
    await execute(
        delete(result_chart).where(
            result_chart.c.analysis_result_id == analysis_result_id),
        commit_after=True
    )
    await execute(
        delete(result_table).where(
            result_table.c.analysis_result_id == analysis_result_id),
        commit_after=True
    )
    # await execute(
    #     delete(aggregation_object).where(
    #         aggregation_object.c.analysis_result_id == analysis_result_id),
    #     commit_after=True
    # )

    await execute(
        delete(analysis_result).where(
            analysis_result.c.id == analysis_result_id),
        commit_after=True
    )


async def get_analysis_result_by_id(analysis_result_id: uuid.UUID) -> AnalysisResult:
    result = await fetch_one(
        select(analysis_result).where(
            analysis_result.c.id == analysis_result_id)
    )

    if result is None:
        return None

    # Get image URLs
    images = await fetch_all(
        select(result_image).where(
            result_image.c.analysis_result_id == analysis_result_id
        )
    )
    result["image_urls"] = [img["image_url"] for img in images]

    # Get chart script paths
    charts = await fetch_all(
        select(result_chart).where(
            result_chart.c.analysis_result_id == analysis_result_id
        )
    )
    result["chart_script_paths"] = [chart["chart_script_path"]
                                    for chart in charts]

    # Get table paths
    tables = await fetch_all(
        select(result_table).where(
            result_table.c.analysis_result_id == analysis_result_id
        )
    )
    result["table_paths"] = [table["table_path"] for table in tables]

    return AnalysisResult(**result)


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
        analysis_results_list.append(AnalysisResult(**result))

    # Populate attachments for each result
    for result in analysis_results_list:
        # Get image URLs
        images = await fetch_all(
            select(result_image).where(
                result_image.c.analysis_result_id == result.id
            )
        )
        result.image_urls = [img["image_url"] for img in images]

        # Get chart script paths
        charts = await fetch_all(
            select(result_chart).where(
                result_chart.c.analysis_result_id == result.id
            )
        )
        result.chart_script_paths = [
            chart["chart_script_path"] for chart in charts]

        # Get table paths
        tables = await fetch_all(
            select(result_table).where(
                result_table.c.analysis_result_id == result.id
            )
        )
        result.table_paths = [table["table_path"] for table in tables]

    return analysis_results_list


async def get_analysis_results_by_ids(analysis_result_ids: List[uuid.UUID]) -> List[AnalysisResult]:
    results = await fetch_all(
        select(analysis_result).where(
            analysis_result.c.id.in_(analysis_result_ids))
    )

    analysis_results_list = []
    for result in results:
        analysis_results_list.append(AnalysisResult(**result))

    # Get all attachments for these results
    images = await fetch_all(
        select(result_image).where(
            result_image.c.analysis_result_id.in_(analysis_result_ids)
        )
    )
    charts = await fetch_all(
        select(result_chart).where(
            result_chart.c.analysis_result_id.in_(analysis_result_ids)
        )
    )
    tables = await fetch_all(
        select(result_table).where(
            result_table.c.analysis_result_id.in_(analysis_result_ids)
        )
    )

    # Populate each result's attachments
    for result in analysis_results_list:
        result.image_urls = [img["image_url"]
                             for img in images if img["analysis_result_id"] == result.id]
        result.chart_script_paths = [chart["chart_script_path"]
                                     for chart in charts if chart["analysis_result_id"] == result.id]
        result.table_paths = [table["table_path"]
                              for table in tables if table["analysis_result_id"] == result.id]

    return analysis_results_list


async def update_analysis_result(analysis_result_arg: AnalysisResult) -> AnalysisResult:
    update_data = AnalysisResultInDB(**analysis_result_arg.model_dump())

    await execute(
        update(analysis_result).where(analysis_result.c.id == analysis_result_arg.id).values(
            **update_data.model_dump()
        ),
        commit_after=True
    )

    # Delete existing attachments
    await execute(
        delete(result_image).where(
            result_image.c.analysis_result_id == analysis_result_arg.id),
        commit_after=True
    )
    await execute(
        delete(result_chart).where(
            result_chart.c.analysis_result_id == analysis_result_arg.id),
        commit_after=True
    )
    await execute(
        delete(result_table).where(
            result_table.c.analysis_result_id == analysis_result_arg.id),
        commit_after=True
    )

    # Batch insert image URLs
    if analysis_result_arg.image_urls:
        image_values = [
            {
                "id": uuid.uuid4(),
                "analysis_result_id": analysis_result_arg.id,
                "image_url": image_url
            }
            for image_url in analysis_result_arg.image_urls
        ]
        await execute(
            insert(result_image).values(image_values),
            commit_after=True
        )

    # Batch insert chart script paths
    if analysis_result_arg.chart_script_paths:
        chart_values = [
            {
                "id": uuid.uuid4(),
                "analysis_result_id": analysis_result_arg.id,
                "chart_script_path": chart_script_path
            }
            for chart_script_path in analysis_result_arg.chart_script_paths
        ]
        await execute(
            insert(result_chart).values(chart_values),
            commit_after=True
        )

    # Batch insert table paths
    if analysis_result_arg.table_paths:
        table_values = [
            {
                "id": uuid.uuid4(),
                "analysis_result_id": analysis_result_arg.id,
                "table_path": table_path
            }
            for table_path in analysis_result_arg.table_paths
        ]
        await execute(
            insert(result_table).values(table_values),
            commit_after=True
        )

    return analysis_result_arg
