import uuid
from sqlalchemy import update, select, insert, delete
from typing import List


from synesis_api.database.service import execute, fetch_one, fetch_all
from synesis_api.modules.analysis.models import (
    analysis,
    analysis_result,
    notebook_section,
    result_image,
    result_echart,
    result_table,
)
from synesis_schemas.main_server import (
    AnalysisResult,
    AnalysisResultInDB,
    AnalysisResultVisualizationCreate
)
from synesis_api.modules.analysis.service.service_utils import (
    get_last_element_in_section,
    get_prev_element,
)
from synesis_api.modules.visualization.service import create_images, create_echarts, create_tables
from synesis_schemas.main_server import ImageCreate, EchartCreate, TableCreate


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

    if analysis_result_arg.image_ids:
        result_image_records = [{"id": uuid.uuid4(
        ), "analysis_result_id": analysis_result_in_db.id, "image_id": image_id} for image_id in analysis_result_arg.image_ids]
        await execute(
            insert(result_image).values(result_image_records), commit_after=True
        )
    if analysis_result_arg.echart_ids:
        result_echart_records = [{"id": uuid.uuid4(), "analysis_result_id": analysis_result_in_db.id,
                                  "echart_id": echart_id} for echart_id in analysis_result_arg.echart_ids]
        await execute(
            insert(result_echart).values(result_echart_records), commit_after=True
        )
    if analysis_result_arg.table_ids:
        result_table_records = [{"id": uuid.uuid4(
        ), "analysis_result_id": analysis_result_in_db.id, "table_id": table_id} for table_id in analysis_result_arg.table_ids]
        await execute(
            insert(result_table).values(result_table_records),
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
        delete(result_echart).where(
            result_echart.c.analysis_result_id == analysis_result_id),
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
    result["image_ids"] = [img["image_id"] for img in images]

    # Get chart script paths
    charts = await fetch_all(
        select(result_echart).where(
            result_echart.c.analysis_result_id == analysis_result_id
        )
    )
    result["echart_ids"] = [chart["echart_id"]
                            for chart in charts]

    # Get table paths
    tables = await fetch_all(
        select(result_table).where(
            result_table.c.analysis_result_id == analysis_result_id
        )
    )
    result["table_ids"] = [table["table_id"] for table in tables]

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
        result.image_ids = [img["image_id"] for img in images]

        # Get chart script paths
        charts = await fetch_all(
            select(result_echart).where(
                result_echart.c.analysis_result_id == result.id
            )
        )
        result.echart_ids = [
            chart["echart_id"] for chart in charts]

        # Get table paths
        tables = await fetch_all(
            select(result_table).where(
                result_table.c.analysis_result_id == result.id
            )
        )
        result.table_ids = [table["table_id"] for table in tables]

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
        select(result_echart).where(
            result_echart.c.analysis_result_id.in_(analysis_result_ids)
        )
    )
    tables = await fetch_all(
        select(result_table).where(
            result_table.c.analysis_result_id.in_(analysis_result_ids)
        )
    )

    # Populate each result's attachments
    for result in analysis_results_list:
        result.image_ids = [img["image_id"]
                            for img in images if img["analysis_result_id"] == result.id]
        result.echart_ids = [chart["echart_id"]
                             for chart in charts if chart["analysis_result_id"] == result.id]
        result.table_ids = [table["table_id"]
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
        delete(result_echart).where(
            result_echart.c.analysis_result_id == analysis_result_arg.id),
        commit_after=True
    )
    await execute(
        delete(result_table).where(
            result_table.c.analysis_result_id == analysis_result_arg.id),
        commit_after=True
    )

    # Batch insert image URLs
    if analysis_result_arg.image_ids:
        result_image_records = [
            {"id": uuid.uuid4(), "analysis_result_id": analysis_result_arg.id, "image_id": image_id} for image_id in analysis_result_arg.image_ids]

        await execute(
            insert(result_image).values(result_image_records),
            commit_after=True
        )

    # Batch insert chart script paths
    if analysis_result_arg.echart_ids:
        result_echart_records = [
            {"id": uuid.uuid4(), "analysis_result_id": analysis_result_arg.id, "echart_id": echart_id} for echart_id in analysis_result_arg.echart_ids]

        await execute(
            insert(result_echart).values(result_echart_records),
            commit_after=True
        )

    # Batch insert table paths
    if analysis_result_arg.table_ids:
        result_table_records = [
            {"id": uuid.uuid4(), "analysis_result_id": analysis_result_arg.id, "table_id": table_id} for table_id in analysis_result_arg.table_ids]

        await execute(
            insert(result_table).values(result_table_records),
            commit_after=True
        )

    return analysis_result_arg


async def create_analysis_result_visualization(analysis_result_visualization_create: AnalysisResultVisualizationCreate) -> None:
    image_objs = await create_images(analysis_result_visualization_create.image_creates)
    echart_objs = await create_echarts(analysis_result_visualization_create.echart_creates)
    table_objs = await create_tables(analysis_result_visualization_create.table_creates)

    result_image_records = [
        {"id": uuid.uuid4(), "analysis_result_id": analysis_result_visualization_create.analysis_result_id, "image_id": image_obj.id} for image_obj in image_objs]
    result_echart_records = [
        {"id": uuid.uuid4(), "analysis_result_id": analysis_result_visualization_create.analysis_result_id, "echart_id": echart_obj.id} for echart_obj in echart_objs]
    result_table_records = [
        {"id": uuid.uuid4(), "analysis_result_id": analysis_result_visualization_create.analysis_result_id, "table_id": table_obj.id} for table_obj in table_objs]

    await execute(
        insert(result_image).values(result_image_records),
        commit_after=True
    )
    await execute(
        insert(result_echart).values(result_echart_records),
        commit_after=True
    )
    await execute(
        insert(result_table).values(result_table_records),
        commit_after=True
    )
