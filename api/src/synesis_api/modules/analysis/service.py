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


async def run_eda_agent(
        eda_job_id: uuid.UUID,
        dataset_id: uuid.UUID,
        data_path: str,
        data_description: str,
        problem_description: str,
        data_type: str = "time_series",
) -> EDAJobResultInDB:
    try: 
        try:
            async with aiofiles.open(data_path, 'r', encoding="utf-8") as f:
                content = await f.read()
                df = pd.read_csv(StringIO(content))
        except:
            raise HTTPException(
                status_code=404, detail=f"File in {data_path} not found")

        logger.info("Data loaded")

        try:
            logger.info("Creating EDA agent")
            eda_agent = EDAAgent(df, data_type, data_description, problem_description, Path(data_path))
            logger.info("Running full analysis")
            response = await eda_agent.run_full_analysis()
            logger.info("Full analysis completed")
        except:
            raise HTTPException(status_code=500, detail="Failed during eda")


        output_in_db = EDAJobResultInDB(
            job_id=eda_job_id,
            dataset_id=dataset_id,
            **response.model_dump()
        )

        eda_exist = await fetch_one(
            select(eda_jobs_results).where(eda_jobs_results.c.dataset_id == dataset_id)
        )
        
        if eda_exist:
            logger.info("Updating existing EDA result")
            logger.info(output_in_db)
            await execute(
                update(eda_jobs_results)
                .where(eda_jobs_results.c.dataset_id == dataset_id)
                .values(
                    # should we update the id since we are creating a new job?
                    basic_eda=output_in_db.basic_eda,
                    advanced_eda=output_in_db.advanced_eda,
                    independent_eda=output_in_db.independent_eda,
                    python_code=output_in_db.python_code
                ),
                commit_after=True
            )
        else:
            logger.info("Creating new EDA result")
            await execute(
                insert(eda_jobs_results).values(output_in_db.model_dump()),
                commit_after=True
            )

        # update job to completed
        await update_job_status(eda_job_id, "completed")
        logger.info("Job updated in DB")

    except Exception as e:
        logger.error(f"Error running integration agent: {e}")

    # update job to completed
    try:
        await execute(
            update(jobs).where(jobs.c.id == eda_job_id).values(
                status="completed", completed_at=datetime.now(timezone.utc)),
            commit_after=True
        )
    except:
        logger.info("Job updated in DB")
        await update_job_status(eda_job_id, "failed")

    return output_in_db


@shared_task
def run_eda_job(
    eda_job_id: uuid.UUID,
    dataset_id: uuid.UUID,
    data_path: str,
    data_description: str,
    problem_description: str,
    data_type: str = "time_series",
):

    loop = asyncio.get_event_loop()
    loop.run_until_complete(run_eda_agent(eda_job_id, dataset_id, data_path,
                                          data_description, problem_description, data_type))


async def get_job_results(job_id: uuid.UUID) -> EDAJobResultInDB:

    metadata = await get_job_metadata(job_id)

    if metadata.status != "completed":
        raise HTTPException(status_code=400, detail="Job is not completed")

    data = await fetch_one(
        select(eda_jobs_results).where(eda_jobs_results.c.job_id == job_id),
        commit_after=True
    )

    return EDAJobResultInDB(**data)


async def create_pdf_from_results(job_results: EDAJobResultInDB, eda_job_id: uuid.UUID) -> None:
    
    file_html = save_markdown_as_html(job_results.summary)
    logger.info("HTML file saved")

    file = None
    await upload_object_s3(file, "synesis-eda", f"{eda_job_id}.html")
    logger.info("Results uploaded to S3")
