import uuid
import asyncio
import numpy as np
import pandas as pd
from pathlib import Path
from celery import shared_task
from datetime import datetime
from fastapi import HTTPException
from celery.utils.log import get_task_logger
from sqlalchemy import select, insert, update
from ..ontology.models import time_series, time_series_dataset
from ..ontology.schema import TimeSeries, TimeSeriesDataset
from .schema import (IntegrationJobMetadataInDB,
                     IntegrationJobResultInDB)
from .models import integration_jobs, integration_jobs_results
from ..database.service import execute, fetch_one
from .agent import IntegrationDeps, integration_agent


logger = get_task_logger(__name__)


async def run_integration_agent(
        job_id: uuid.UUID,
        api_key: str,
        data_path: str,
        data_description: str,
) -> IntegrationJobResultInDB:

    try:
        deps = IntegrationDeps(
            api_key=api_key,
            data_path=Path(data_path),
            data_description=data_description
        )

        nodes = []
        async with integration_agent.iter(
            "Restructure and integrate the data",
            deps=deps
        ) as agent_run:

            async for node in agent_run:
                # TODO: Publish the node outputs for agent monitoring
                nodes.append(node)
                logger.info(f"Integration agent state: {node}")

            logger.info(f"Integration agent run completed for job {job_id}")

        agent_output = agent_run.result.data

        output_in_db = IntegrationJobResultInDB(
            job_id=job_id,
            **agent_output.model_dump()
        )

        await execute(
            insert(integration_jobs_results).values(output_in_db.model_dump()),
            commit_after=True
        )

        # Update integration jobs status to completed
        await execute(
            update(integration_jobs).values(
                status="completed", completed_at=datetime.now()),
            commit_after=True
        )

    except Exception as e:
        logger.error(f"Error running integration agent: {e}")

        await execute(
            update(integration_jobs).values(
                status="failed", completed_at=datetime.now()),
            commit_after=True
        )

        if Path(data_path).exists():
            Path(data_path).unlink()

        raise HTTPException(
            status_code=500, detail="Failed to process the integration request")

    else:
        return agent_output


@shared_task
def run_integration_job(job_id: uuid.UUID, api_key: str, data_path: str, data_description: str):
    asyncio.run(run_integration_agent(
        job_id, api_key, data_path, data_description))


async def create_integration_job(user_id: uuid.UUID, api_key_id: uuid.UUID, job_id: uuid.UUID | None = None) -> IntegrationJobMetadataInDB:

    integration_job = IntegrationJobMetadataInDB(
        id=job_id if job_id else uuid.uuid4(),
        user_id=user_id,
        api_key_id=api_key_id,
        status="running",
        started_at=datetime.now()
    )

    await execute(
        insert(integration_jobs).values(integration_job.model_dump()),
        commit_after=True
    )

    return integration_job


async def get_job_metadata(job_id: uuid.UUID) -> IntegrationJobMetadataInDB:

    job = await fetch_one(
        select(integration_jobs).where(integration_jobs.c.id == job_id),
        commit_after=True
    )

    if job is None:
        raise HTTPException(
            status_code=404, detail="Job not found"
        )

    return IntegrationJobMetadataInDB(**job)


async def get_job_results(job_id: uuid.UUID) -> IntegrationJobResultInDB:

    metadata = await get_job_metadata(job_id)

    if metadata.status != "completed":
        raise HTTPException(status_code=400, detail="Job is not completed")

    results = await fetch_one(
        select(integration_jobs_results).where(
            integration_jobs_results.c.job_id == job_id),
        commit_after=True
    )

    return IntegrationJobResultInDB(**results)


def validate_restructured_data(data: pd.DataFrame, index_first_level: str, index_second_level: str | None) -> pd.DataFrame | None:

    if index_first_level not in data.columns:
        raise HTTPException(
            status_code=400,
            detail=f"Invalid data: First level index column '{index_first_level}' not found in DataFrame"
        )

    if index_second_level:
        if index_second_level not in data.columns:
            raise HTTPException(
                status_code=400,
                detail=f"Invalid data: Second level index column '{index_second_level}' not found in DataFrame"
            )
        data = data.set_index([index_first_level, index_second_level])
    else:
        data = data.set_index(index_first_level)

    return data


async def insert_restructured_time_series_data_to_db(
        df: pd.DataFrame,
        data_description: str,
        dataset_name: str,
        data_modality: str,
        user_id: uuid.UUID) -> uuid.UUID:

    if data_modality != "time_series":
        raise HTTPException(
            status_code=400,
            detail="Only time series data is supported at the moment"
        )

    # Calculate dataset statistics
    is_multi_series = df.index.nlevels > 1
    unique_series = df.index.get_level_values(0).unique()

    if is_multi_series:
        series_counts = df.groupby(level=0).size()
        num_series = len(unique_series)
    else:
        series_counts = np.array([len(df.index)])
        num_series = 1

    # Create and store dataset
    dataset_id = uuid.uuid4()
    dataset = TimeSeriesDataset(
        id=dataset_id,
        name=dataset_name,
        description=data_description,
        user_id=user_id,
        num_series=num_series,
        num_features=len(df.columns),
        avg_num_timestamps=int(series_counts.mean()),
        max_num_timestamps=int(series_counts.max()),
        min_num_timestamps=int(series_counts.min()),
        index_first_level=df.index.names[0],
        index_second_level=df.index.names[1] if len(
            df.index.names) > 1 else None,
        created_at=datetime.now(),
        updated_at=datetime.now()
    )

    await execute(
        insert(time_series_dataset).values(dataset.model_dump()),
        commit_after=True
    )

    # Create and store time series
    if is_multi_series:
        for original_id in unique_series:
            series_data = df.loc[original_id]
            series_id = uuid.uuid4()

            time_series_record = TimeSeries(
                id=series_id,
                description=f"Time series {series_id}",
                features=list(df.columns),
                num_timestamps=len(series_data),
                num_features=len(df.columns),
                start_timestamp=series_data.index.min(),
                end_timestamp=series_data.index.max(),
                dataset_id=dataset_id,
                original_id=str(original_id),
                created_at=datetime.now(),
                updated_at=datetime.now()
            )

            await execute(
                insert(time_series).values(time_series_record.model_dump()),
                commit_after=True
            )
    else:
        series_id = uuid.uuid4()
        time_series_record = TimeSeries(
            id=series_id,
            description=data_description,
            features=list(df.columns),
            num_timestamps=len(df),
            num_features=len(df.columns),
            start_timestamp=df.index.min(),
            end_timestamp=df.index.max(),
            dataset_id=dataset_id,
            original_id=None,
            created_at=datetime.now(),
            updated_at=datetime.now()
        )

        await execute(
            insert(time_series).values(time_series_record.model_dump()),
            commit_after=True
        )

    return dataset_id
