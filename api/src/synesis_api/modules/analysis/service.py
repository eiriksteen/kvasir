import uuid
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
analysis_execution_agent = AnalysisExecutionAgent(eda_cs_tools)

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
    user_id: uuid.UUID,
    datasets: List[Dataset],
    # automations: List[Automation],
    problem_description: str,
    prompt: str,
    analysis_job_result: AnalysisJobResultMetadataInDB | None = None,
) -> AnalysisJobResultMetadataInDB:
    
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
        if analysis_job_result is not None:
            prompt = "You create this analysis plan: " + json.dumps(analysis_job_result.analysis_plan.model_dump()) + "The user's feedback: " + prompt + "Change the analysis plan to reflect these wishes."
        response = await analysis_planner_agent.run_analysis_planner(
            dfs,
            problem_description,
            datasets,
            eda_cs_tools_str,
            prompt
        )

        logger.info(f"Analysis planner completed")
        logger.info(response)
        analysis_plan = AnalysisPlan(**response.model_dump())
    except Exception as e:
        raise HTTPException(
            status_code=500,
            detail=f"Error running analysis planner: {str(e)}"
        )
    
    analysis_job_result_metadata_in_db = AnalysisJobResultMetadataInDB(
                job_id=job_id,
                user_id=user_id,
                number_of_datasets=len(datasets),
                number_of_automations=0, # TODO: add automations
                analysis_plan=analysis_plan, # Store the full analysis plan object
                created_at=datetime.now(),
                pdf_created=False,
                pdf_s3_path=None
            )

    try:
        if analysis_job_result is None:
            logger.info("Inserting analysis plan into DB")

            # Insert dataset mappings
            for dataset in datasets:
                await execute(
                    insert(analysis_jobs_datasets).values(
                        job_id=job_id,
                        dataset_id=dataset.id
                    ),
                    commit_after=True
                )

            await execute(
                insert(analysis_jobs_results).values(
                    **analysis_job_result_metadata_in_db.model_dump()
                ),
                commit_after=True
            )

            await update_job_status(job_id, "completed")

            logger.info("Analysis plan inserted into DB")

            return analysis_job_result_metadata_in_db
        
        else:
            logger.info("Updating analysis plan in DB")
            
            await execute(
                update(analysis_jobs_results).values(
                    **analysis_job_result_metadata_in_db.model_dump()
                ),
                commit_after=True
            )
            
            await update_job_status(job_id, "completed")

            logger.info("Analysis plan updated in DB")

            return analysis_job_result_metadata_in_db
    
    except Exception as e:
        raise HTTPException(
            status_code=500,
            detail=f"Error inserting analysis plan into DB: {str(e)}"
        )


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

async def run_simple_analysis_job(
    datasets: List[Dataset],    
    prompt: str,
    data_paths: List[Path],
    message_history: List[ModelMessage]
):
    dfs = [] # we should store column names in the dataset object
    yield "Loading datasets and checking cache..."
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
        logger.info(f"Start running simple analysis")
        yield "Running analysis..."
        async for progress in analysis_execution_agent.simple_analysis_stream(
            dfs,
            prompt,
            data_paths,
            message_history
        ):
            yield progress
        logger.info(f"Simple analysis completed")
    except Exception as e:
        raise HTTPException(
            status_code=500,
            detail=f"Error running simple analysis: {str(e)}"
        )


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
    user_id: uuid.UUID,
    datasets: List[Dataset],
    # automations: List[Automation],
    problem_description: str,
    prompt: str,
    analysis_job_result: AnalysisJobResultMetadataInDB | None = None,
) -> AnalysisJobResultMetadataInDB:
    return await run_analysis_planner(job_id, user_id, datasets, problem_description, prompt, analysis_job_result) # TODO: add automations


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


async def get_analysis_job_results_from_db(job_id: uuid.UUID) -> AnalysisJobResultMetadataInDB:
    result = await fetch_one(
        select(analysis_jobs_results).where(analysis_jobs_results.c.job_id == job_id),
        commit_after=True
    )

    if result is None:
        raise HTTPException(
            status_code=404, detail="Analysis job results not found"
        )

    return AnalysisJobResultMetadataInDB(**result)


async def get_user_analyses_by_ids(user_id: uuid.UUID, analysis_ids: List[uuid.UUID]) -> AnalysisJobResultMetadataList:
    data = await fetch_all(
        select(analysis_jobs_results).where(analysis_jobs_results.c.user_id == user_id, analysis_jobs_results.c.job_id.in_(analysis_ids))
    )
    return [AnalysisJobResultMetadataInDB(**d) for d in data]

async def get_dataset_ids_by_job_id(job_id: uuid.UUID) -> List[uuid.UUID]:
    dataset_mappings = await fetch_all(
        select(analysis_jobs_datasets).where(analysis_jobs_datasets.c.job_id == job_id)
    )
    
    return [mapping["dataset_id"] for mapping in dataset_mappings]