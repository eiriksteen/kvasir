import uuid
import aiofiles
from io import StringIO
import uuid
import pandas as pd
from datetime import datetime
from pathlib import Path
from fastapi import HTTPException
from sqlalchemy import select, insert, update
from ..database.service import execute, fetch_one
from ..ontology.models import time_series, time_series_dataset
from ..ontology.schema import TimeSeries, TimeSeriesDataset
from .schema import EDAJobMetaDataInDB, EDAJobResultInDB
from .models import eda_jobs, eda_jobs_results
from .agent.agent import eda_basic_agent, eda_advanced_agent, eda_independent_agent, eda_summary_agent
from .agent.deps import EDADepsBasic, EDADepsAdvanced, EDADepsIndependent, EDADepsSummary
from .agent.prompt import BASIC_PROMPT, ADVANCED_PROMPT, INDEPENDENT_PROMPT, SUMMARIZE_EDA
from ..utils import save_markdown_as_html

# task logger?

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
            content = await f.read()  # Read file content asynchronously
            df = pd.read_csv(StringIO(content)) 
    except:
        raise HTTPException(status_code=404, detail=f"File in {data_path} not found")
    
    print("1")
    try: 
        eda_deps_basic = EDADepsBasic(
            df=df,
            data_description=data_description,
            data_type=data_type,
            problem_description=problem_description,
            api_key=None,
        )
        print("2")
        basic_eda = await eda_basic_agent.run(
            user_prompt=BASIC_PROMPT,
            deps=eda_deps_basic
        )

        eda_deps_advanced = EDADepsAdvanced(
            df=df,
            data_description=data_description,
            data_type=data_type,
            problem_description=problem_description,
            api_key=None,
            basic_data_analysis=basic_eda.data.detailed_summary
        )
        print("3")
        advanced_eda = await eda_advanced_agent.run(
            user_prompt=ADVANCED_PROMPT,
            deps=eda_deps_advanced
        )

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
        print("4")
        independent_eda = await eda_independent_agent.run(
            user_prompt=INDEPENDENT_PROMPT,
            deps=eda_deps_independent
        )
        print("4.5")
    except:
        raise HTTPException(status_code=500, detail="Failed during independent eda")

    try: 
        print("EDA Complete")
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
    except:
        raise HTTPException(status_code=500, detail="Failed in summary of eda")
    
    
    print("4.7")
    output_in_db = EDAJobResultInDB(
        job_id=eda_job_id,
        **summary.data.model_dump()
    )

    print("5")
    # Write an html of the summary
    user_dir = Path("files") / f"{user_id}"
    user_dir.mkdir(parents=True, exist_ok=True)
    output_path = user_dir / f"{eda_job_id}.html"

    print("6")
    await save_markdown_as_html(output_in_db.detailed_summary, output_path)

    print("7")

    # insert results into db
    await execute(
        insert(eda_jobs_results).values(output_in_db.model_dump()),
        commit_after=True
    )

    print("8")
    # update job to completed
    await execute(
        update(eda_jobs).where(eda_jobs.c.id == eda_job_id).values(
            status="completed", completed_at=datetime.now()),
            commit_after=True
    )
    
    return output_in_db



async def get_job_metadata(eda_id: uuid.UUID) -> EDAJobMetaDataInDB:
    job = await fetch_one(
        select(eda_jobs).where(eda_jobs.c.id == eda_id),
        commit_after=True
    )

    if job is None:
        raise HTTPException(
            status_code=404, detail="Job not found"
        )

    return EDAJobMetaDataInDB(**job)


async def get_job_results(job_id: uuid.UUID) -> EDAJobResultInDB:

    metadata = await get_job_metadata(job_id)

    if metadata.status != "completed":
        raise HTTPException(status_code=400, detail="Job is not completed")

    results = await fetch_one(
        select(eda_jobs_results).where(
            eda_jobs_results.c.job_id == job_id),
        commit_after=True
    )

    return EDAJobResultInDB(**results)

async def create_eda_job(user_id: uuid.UUID, api_key_id: uuid.UUID = None, job_id: uuid.UUID = None) -> EDAJobMetaDataInDB:
    eda_job = EDAJobMetaDataInDB(
        id = job_id if job_id else uuid.uuid4(),
        status="running",
        api_key_id=api_key_id if api_key_id else uuid.uuid4(),
        user_id=user_id,
        started_at=datetime.now()
    )
    await execute(
        insert(eda_jobs).values(eda_job.model_dump()),
        commit_after=True
    )
    return eda_job