import uuid
from sqlalchemy import update, select, insert, delete
from typing import List


from synesis_api.database.service import execute, fetch_one, fetch_all
from synesis_api.modules.analysis.models import (
    analysis,
    analysis_result,
    dataset_in_analysis,
    notebook_section,
    data_source_in_analysis,
)
# from synesis_api.modules.data_objects.models import aggregation_object
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

    for plot_url in analysis_result_arg.plot_urls:
        await execute(
            insert(plot).values(
                id=uuid.uuid4(),
                analysis_result_id=analysis_result_in_db.id,
                plot_url=plot_url
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
        delete(plot).where(plot.c.analysis_result_id == analysis_result_id),
        commit_after=True
    )
    await execute(
        delete(table).where(table.c.analysis_result_id == analysis_result_id),
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

    plot_urls = await fetch_all(
        select(plot).where(
            plot.c.analysis_result_id == analysis_result_id
        )
    )
    result["plot_urls"] = [plot_in_db["plot_url"] for plot_in_db in plot_urls]

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
        for result in analysis_results_list:
            plot_urls = await fetch_all(
                select(plot).where(
                    plot.c.analysis_result_id == result.id
                )
            )
            result.plot_urls = [plot_in_db["plot_url"]
                                for plot_in_db in plot_urls]

    return analysis_results_list


async def get_analysis_results_by_ids(analysis_result_ids: List[uuid.UUID]) -> List[AnalysisResult]:
    results = await fetch_all(
        select(analysis_result).where(
            analysis_result.c.id.in_(analysis_result_ids))
    )

    analysis_results_list = []
    for result in results:
        analysis_results_list.append(AnalysisResult(**result))

    plot_urls = await fetch_all(
        select(plot).where(
            plot.c.analysis_result_id.in_(analysis_result_ids)
        )
    )
    for result in analysis_results_list:
        result.plot_urls = [plot_in_db["plot_url"]
                            for plot_in_db in plot_urls if plot_in_db["analysis_result_id"] == result.id]

    return analysis_results_list


async def update_analysis_result(analysis_result_arg: AnalysisResult) -> AnalysisResult:
    update_data = AnalysisResultInDB(**analysis_result_arg.model_dump())

    await execute(
        update(analysis_result).where(analysis_result.c.id == analysis_result_arg.id).values(
            **update_data.model_dump()
        ),
        commit_after=True
    )

    await execute(
        delete(plot).where(plot.c.analysis_result_id == analysis_result_arg.id),
        commit_after=True
    )

    for plot_url in analysis_result_arg.plot_urls:
        await execute(
            insert(plot).values(
                id=uuid.uuid4(),
                analysis_result_id=analysis_result_arg.id,
                plot_url=plot_url
            ),
            commit_after=True
        )

    return analysis_result_arg
