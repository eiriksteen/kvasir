import uuid
from fastapi import HTTPException
from sqlalchemy import update, select, insert, delete
from typing import List
from ...database.service import execute, fetch_one, fetch_all
from .models import analysis_jobs_results, analysis_jobs_datasets, analysis_jobs_automations, analysis_status_messages
from .schema import AnalysisJobResultMetadataInDB, AnalysisJobResultInDB, AnalysisPlan, AnalysisJobResultMetadataList, AnalysisJobResult, AnalysisStatusMessage
from ..jobs.service import update_job_status
from ...utils import save_markdown_as_html
from ...aws.service import upload_object_s3
from ...worker import logger
from ..jobs.service import delete_job_by_id
from ..chat.models import analysis_context


async def run_analysis_execution(
        job_id: uuid.UUID,
        dataset_ids: List[uuid.UUID],
        automation_ids: List[uuid.UUID],
        data_paths: List[str],
        data_description: str,
        problem_description: str,
        analysis_plan: AnalysisPlan,
        data_type: str = "time_series",
) -> AnalysisJobResultInDB:
    pass

    # try: 
    #     dfs = []
    #     try:
    #         for data_path in data_paths:
    #             async with aiofiles.open(data_path, 'r', encoding="utf-8") as f:
    #                 content = await f.read()
    #                 df = pd.read_csv(StringIO(content))
    #                 dfs.append(df)
    #     except:
    #         raise HTTPException(
    #             status_code=404, detail=f"File in {data_path} not found")

    #     logger.info("Data loaded")

    #     try:
    #         logger.info("Creating EDA agent")
    #         eda_agent = EDAAgent(df, data_type, data_description, problem_description, Path(data_path))
    #         logger.info("Running full analysis")
    #         response = await eda_agent.run_full_analysis()
    #         logger.info("Full analysis completed")
    #     except:
    #         raise HTTPException(status_code=500, detail="Failed during eda")

    #     output_in_db = EDAJobResultInDB(
    #         job_id=eda_job_id,
    #         dataset_id=dataset_id,
    #         **response.model_dump()
    #     )

    #     eda_exist = await fetch_one(
    #         select(analysis_jobs_results).where(analysis_jobs_results.c.dataset_id == dataset_id)
    #     )
        
    #     if eda_exist:
    #         logger.info("Updating existing EDA result")
    #         logger.info(output_in_db)
    #         await execute(
    #             update(eda_jobs_results)
    #             .where(eda_jobs_results.c.dataset_id == dataset_id)
    #             .values(
    #                 # should we update the id since we are creating a new job?
    #                 basic_eda=output_in_db.basic_eda,
    #                 advanced_eda=output_in_db.advanced_eda,
    #                 independent_eda=output_in_db.independent_eda,
    #                 python_code=output_in_db.python_code
    #             ),
    #             commit_after=True
    #         )
    #     else:
    #         logger.info("Creating new EDA result")
    #         await execute(
    #             insert(eda_jobs_results).values(output_in_db.model_dump()),
    #             commit_after=True
    #         )

    #     # update job to completed
    #     await update_job_status(eda_job_id, "completed")
    #     logger.info("Job updated in DB")

    # except Exception as e:
    #     logger.error(f"Error running integration agent: {e}")

    #     await update_job_status(eda_job_id, "failed")

    #     raise e

    # return output_in_db



async def create_pdf_from_results(job_results: AnalysisJobResultInDB, eda_job_id: uuid.UUID) -> None:
    
    file_html = save_markdown_as_html(job_results.summary)
    # logger.info("HTML file saved")

    file = None
    await upload_object_s3(file, "synesis-eda", f"{eda_job_id}.html")
    # logger.info("Results uploaded to S3")



async def get_status_messages_by_job_id(job_id: uuid.UUID) -> List[AnalysisStatusMessage]:
    messages = await fetch_all(
        select(analysis_status_messages).where(analysis_status_messages.c.job_id == job_id)
    )
    return [AnalysisStatusMessage(**msg) for msg in messages]

async def insert_analysis_job_results_into_db(job_results: AnalysisJobResultMetadataInDB) -> None:
    try:
        logger.info("Inserting analysis plan into DB")

        # Insert dataset mappings
        for dataset_id in job_results.dataset_ids:
            await execute(
                insert(analysis_jobs_datasets).values(
                    job_id=job_results.job_id,
                    dataset_id=dataset_id
                ),
                commit_after=True
            )

        # Insert status messages
        for status_message in job_results.status_messages:
            await execute(
                insert(analysis_status_messages).values(
                    **status_message.model_dump()
                ),
                commit_after=True
            )

        # Create a dict without dataset_ids, automation_ids, and status_messages
        db_data = job_results.model_dump(exclude={'dataset_ids', 'automation_ids', 'status_messages'})
        await execute(
            insert(analysis_jobs_results).values(
                **db_data
            ),
            commit_after=True
        )

        await update_job_status(job_results.job_id, "completed")

        logger.info("Analysis plan inserted into DB")
    except Exception as e:
        logger.info(job_results)
        raise HTTPException(
            status_code=500,
            detail=f"Error inserting analysis plan into DB: {str(e)}"
        )

async def update_analysis_job_results_in_db(job_results: AnalysisJobResultMetadataInDB) -> None:
    try:
        logger.info("Updating analysis plan in DB")
        
        for status_message in job_results.status_messages:
            await execute(
                insert(analysis_status_messages).values(
                    **status_message.model_dump()
                ),
                commit_after=True
            )

        # Create a dict without dataset_ids, automation_ids, and status_messages
        db_data = job_results.model_dump(exclude={'dataset_ids', 'automation_ids', 'status_messages'})
        await execute(
            update(analysis_jobs_results)
            .where(analysis_jobs_results.c.job_id == job_results.job_id)
            .values(
                **db_data
            ),
            commit_after=True
        )

        await update_job_status(job_results.job_id, "completed")

        logger.info("Analysis plan updated in DB")

    except Exception as e:
        raise HTTPException(
            status_code=500,
            detail=f"Error updating analysis plan in DB: {str(e)}"
        )



async def get_user_analysis_metadata(user_id: uuid.UUID) -> AnalysisJobResultMetadataList:
    data = await fetch_all(
        select(analysis_jobs_results).where(analysis_jobs_results.c.user_id == user_id)
    )
    
    results = []
    for d in data:
        dataset_ids = await get_dataset_ids_by_job_id(d["job_id"])
        automation_ids = []  # TODO: implement get_automation_ids_by_job_id
        status_messages = await get_status_messages_by_job_id(d["job_id"])
        results.append(AnalysisJobResultMetadataInDB(**d, dataset_ids=dataset_ids, automation_ids=automation_ids, status_messages=status_messages))
    
    return AnalysisJobResultMetadataList(analyses_job_results=results)


async def get_analysis_job_results_from_db(job_id: uuid.UUID) -> AnalysisJobResultMetadataInDB:
    result = await fetch_one(
        select(analysis_jobs_results).where(analysis_jobs_results.c.job_id == job_id),
        commit_after=True
    )

    if result is None:
        raise HTTPException(
            status_code=404, detail="Analysis job results not found"
        )

    dataset_ids = await get_dataset_ids_by_job_id(job_id)
    automation_ids = []
    status_messages = await get_status_messages_by_job_id(job_id)

    return AnalysisJobResultMetadataInDB(**result, dataset_ids=dataset_ids, automation_ids=automation_ids, status_messages=status_messages)


async def get_user_analyses_by_ids(user_id: uuid.UUID, analysis_ids: List[uuid.UUID]) -> AnalysisJobResultMetadataList:
    data = await fetch_all(
        select(analysis_jobs_results).where(analysis_jobs_results.c.user_id == user_id, analysis_jobs_results.c.job_id.in_(analysis_ids))
    )
    
    results = []
    for d in data:
        dataset_ids = await get_dataset_ids_by_job_id(d["job_id"])
        automation_ids = []  # TODO: implement get_automation_ids_by_job_id
        status_messages = await get_status_messages_by_job_id(d["job_id"])
        results.append(AnalysisJobResultMetadataInDB(**d, dataset_ids=dataset_ids, automation_ids=automation_ids, status_messages=status_messages))
    
    return AnalysisJobResultMetadataList(analyses_job_results=results)

async def get_dataset_ids_by_job_id(job_id: uuid.UUID) -> List[uuid.UUID]:
    dataset_mappings = await fetch_all(
        select(analysis_jobs_datasets).where(analysis_jobs_datasets.c.job_id == job_id)
    )
    
    return [mapping["dataset_id"] for mapping in dataset_mappings]  


async def delete_analysis_job_results_from_db(job_id: uuid.UUID) -> uuid.UUID:
    # TODO: use cascading delete

    # Delete from child tables first
    await execute(
        delete(analysis_jobs_datasets).where(analysis_jobs_datasets.c.job_id == job_id),
        commit_after=True
    )
    await execute(
        delete(analysis_jobs_automations).where(analysis_jobs_automations.c.job_id == job_id),
        commit_after=True
    )
    # Delete status messages
    await execute(
        delete(analysis_status_messages).where(analysis_status_messages.c.job_id == job_id),
        commit_after=True
    )
    # Delete from analysis_context
    await execute(
        delete(analysis_context).where(analysis_context.c.analysis_id == job_id),
        commit_after=True
    )

    # Delete from analysis_jobs_results
    await execute(
        delete(analysis_jobs_results).where(analysis_jobs_results.c.job_id == job_id),
        commit_after=True
    )

    # Delete from jobs table
    await delete_job_by_id(job_id)
    return job_id

    

# async def delete_analysis_job_results_from_db(job_id: uuid.UUID) -> uuid.UUID:
#     # Delete from jobs table - cascading will handle the rest
#     await delete_job_by_id(job_id)
#     return job_id
    
    
