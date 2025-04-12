import uuid
import asyncio
import aiofiles
import pandas as pd
from io import StringIO
from datetime import datetime
from pathlib import Path
from fastapi import HTTPException
from celery import shared_task
from celery.utils.log import get_task_logger
from sqlalchemy import update
from ...database.service import execute
from .schema import EDAJobResultInDB
from .agent import (eda_basic_agent, eda_advanced_agent, eda_independent_agent, eda_summary_agent,
                    EDADepsBasic, EDADepsAdvanced, EDADepsIndependent, EDADepsSummary,
                    BASIC_PROMPT, ADVANCED_PROMPT, INDEPENDENT_PROMPT, SUMMARIZE_EDA)
from ..jobs.models import jobs
from ..jobs.service import get_job_metadata
from ...utils import save_markdown_as_html
from ...aws.service import upload_object_s3, retrieve_object

logger = get_task_logger(__name__)


async def run_eda_agent(
        eda_job_id: uuid.UUID,
        user_id: uuid.UUID,
        data_path: str,
        data_description: str,
        problem_description: str,
        data_type: str = "TimeSeries",
) -> EDAJobResultInDB:

    try:
        async with aiofiles.open(data_path, 'r', encoding="utf-8") as f:
            content = await f.read()
            df = pd.read_csv(StringIO(content))
    except:
        raise HTTPException(
            status_code=404, detail=f"File in {data_path} not found")

    logger.info("Data loaded")

    try:
        eda_deps_basic = EDADepsBasic(
            df=df,
            data_description=data_description,
            data_type=data_type,
            problem_description=problem_description,
            api_key=None,
        )

        basic_eda = await eda_basic_agent.run(
            user_prompt=BASIC_PROMPT,
            deps=eda_deps_basic
        )

        logger.info("Basic EDA completed")

        eda_deps_advanced = EDADepsAdvanced(
            df=df,
            data_description=data_description,
            data_type=data_type,
            problem_description=problem_description,
            api_key=None,
            basic_data_analysis=basic_eda.data.detailed_summary
        )

        advanced_eda = await eda_advanced_agent.run(
            user_prompt=ADVANCED_PROMPT,
            deps=eda_deps_advanced
        )
        logger.info("Advanced EDA completed")
    except:
        raise HTTPException(status_code=500, detail="Failed during eda")

    try:
        eda_deps_independent = EDADepsIndependent(
            data_path=Path(data_path),
            data_description=data_description,
            data_type=data_type,
            problem_description=problem_description,
            api_key=None,
            basic_data_analysis=basic_eda.data.detailed_summary,
            advanced_data_analysis=advanced_eda.data.detailed_summary,
        )
        independent_eda = await eda_independent_agent.run(
            user_prompt=INDEPENDENT_PROMPT,
            deps=eda_deps_independent
        )
        logger.info("Independent EDA completed")
    except:
        raise HTTPException(
            status_code=500, detail="Failed during independent eda")

    try:
        eda_deps_summary = EDADepsSummary(
            data_description=data_description,
            data_type=data_type,
            problem_description=problem_description,
            api_key=None,
            basic_data_analysis=basic_eda.data.detailed_summary,
            advanced_data_analysis=advanced_eda.data.detailed_summary,
            independent_data_analysis=independent_eda.data.detailed_summary,
            python_code=independent_eda.data.python_code,
        )
        summary = await eda_summary_agent.run(
            user_prompt=SUMMARIZE_EDA,
            deps=eda_deps_summary
        )
        logger.info("Summary Completed")
    except:
        raise HTTPException(status_code=500, detail="Failed in summary of eda")

    output_in_db = EDAJobResultInDB(
        job_id=eda_job_id,
        **summary.data.model_dump()
    )

    # Write an html of the summary
    user_dir = Path("files") / f"{user_id}"
    user_dir.mkdir(parents=True, exist_ok=True)
    output_path = user_dir / f"{eda_job_id}.html"

    await save_markdown_as_html(output_in_db.detailed_summary, output_path)
    logger.info("HTML file saved")

    # insert results into db
    await upload_object_s3(output_in_db, "synesis-eda", f"{eda_job_id}.json")
    logger.info("Results uploaded to S3")

    # update job to completed
    await execute(
        update(jobs).where(jobs.c.id == eda_job_id).values(
            status="completed", completed_at=datetime.now()),
        commit_after=True
    )
    logger.info("Job updated in DB")

    return output_in_db


@shared_task
def run_eda_job(
    eda_job_id: uuid.UUID,
    user_id: uuid.UUID,
    data_path: str,
    data_description: str,
    problem_description: str,
    data_type: str = "TimeSeries",
):

    loop = asyncio.get_event_loop()
    loop.run_until_complete(run_eda_agent(eda_job_id, user_id, data_path,
                                          data_description, problem_description, data_type))


async def get_job_results(job_id: uuid.UUID) -> EDAJobResultInDB:

    metadata = await get_job_metadata(job_id)

    if metadata.status != "completed":
        raise HTTPException(status_code=400, detail="Job is not completed")

    json_data = await retrieve_object("synesis-eda", f"{job_id}.json")

    return EDAJobResultInDB(**json_data)
