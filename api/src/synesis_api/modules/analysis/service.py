import uuid
import asyncio
import aiofiles
import pandas as pd
from io import StringIO
from datetime import datetime, timezone
from pathlib import Path
from fastapi import HTTPException
from celery import shared_task
from celery.utils.log import get_task_logger
from sqlalchemy import update
from synesis_api.modules.analysis.schema import EDAJobResultInDB
from synesis_api.modules.jobs.models import jobs
from synesis_api.utils import save_markdown_as_html
from synesis_api.aws.service import upload_object_s3, retrieve_object
from sqlalchemy import update, select, insert
from synesis_api.database.service import execute, fetch_one
from synesis_api.modules.jobs.models import eda_jobs_results
from synesis_api.modules.jobs.service import get_job_metadata, update_job_status


logger = get_task_logger(__name__)

# Add dataset cache
dataset_cache: Dict[str, pd.DataFrame] = {}

analysis_planner_agent = AnalysisPlannerAgent()

async def load_dataset_from_cache_or_disk(dataset_id: uuid.UUID, user_id: uuid.UUID) -> pd.DataFrame:
    """Load dataset from cache if available, otherwise load from disk and cache it."""
    if dataset_id in dataset_cache:
        logger.info(f"Loading dataset from cache: {dataset_id}")
        return dataset_cache[dataset_id]
    data_path = Path(f"integrated_data/{user_id}/{dataset_id}.csv")
    try:
        async with aiofiles.open(data_path, 'r', encoding="utf-8") as f:
            content = await f.read()
            df = pd.read_csv(StringIO(content))
            dataset_cache[data_path] = df
            logger.info(f"Cached dataset: {data_path}")
            return df
    except Exception as e:
        raise HTTPException(
            status_code=404, 
            detail=f"File in {data_path} not found: {str(e)}"
        )

async def run_analysis_planner(
    job_id: uuid.UUID,
    datasets: List[Dataset],
    # automations: List[Automation],
    problem_description: str,
    prompt: str,
) -> AnalysisPlan:
    
    dfs = [] # we should store column names in the dataset object
    try:
        logger.info(f"Start loading datasets")
        for dataset in datasets:
            df = await load_dataset_from_cache_or_disk(dataset.id, dataset.user_id)
            dfs.append(df)
    except Exception as e:
        raise HTTPException(
            status_code=500,
            detail=f"Error loading datasets: {str(e)}"
        )
    try: 
        logger.info(f"Start running analysis planner")
        response = await analysis_planner_agent.run_analysis_planner(
            dfs,
            problem_description,
            datasets,
            eda_cs_tools_str,
            prompt
        )
        logger.info(f"Analysis planner completed")
        output_to_user = AnalysisPlan(response.model_dump())
        return output_to_user
        
    except Exception as e:
        logger.error(f"Error running analysis planner: {e}")
        await update_job_status(job_id, "failed")
        raise e


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


@broker.task
async def run_analysis_execution_job(
    eda_job_id: uuid.UUID,
    dataset_id: uuid.UUID,
    data_path: str,
    data_description: str,
    problem_description: str,
    data_type: str = "time_series",
):
    return await run_analysis_execution(eda_job_id, dataset_id, data_path,
                                          data_description, problem_description, data_type)


@broker.task
async def run_analysis_planner_job(
    job_id: uuid.UUID,
    datasets: List[Dataset],
    # automations: List[Automation],
    problem_description: str,
    prompt: str,
) -> AnalysisPlan:
    return await run_analysis_planner(job_id, datasets, problem_description, prompt) # TODO: add automations


@broker.task
async def test_task():
    logger.info("Test task")

async def get_job_results(job_id: uuid.UUID) -> AnalysisJobResultInDB:

    metadata = await get_job_metadata(job_id)

    if metadata.status != "completed":
        raise HTTPException(status_code=400, detail="Job is not completed")

    data = await fetch_one(
        select(analysis_jobs_results).where(analysis_jobs_results.c.job_id == job_id),
        commit_after=True
    )

    return AnalysisJobResultInDB(**data)


async def create_pdf_from_results(job_results: AnalysisJobResultInDB, eda_job_id: uuid.UUID) -> None:
    
    file_html = save_markdown_as_html(job_results.summary)
    logger.info("HTML file saved")

    file = None
    await upload_object_s3(file, "synesis-eda", f"{eda_job_id}.html")
    logger.info("Results uploaded to S3")



async def get_user_analysis_metadata(user_id: uuid.UUID) -> AnalysisJobResultMetadataList:
    data = await fetch_all(
        select(analysis_jobs_results).where(analysis_jobs_results.c.user_id == user_id)
    )
    return AnalysisJobResultMetadataList(analysis_job_results=[AnalysisJobResultMetadataInDB(**d) for d in data])

