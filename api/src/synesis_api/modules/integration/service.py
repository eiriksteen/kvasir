import uuid
import numpy as np
import pandas as pd
import asyncio
from pathlib import Path
from celery import shared_task
from datetime import datetime
from fastapi import HTTPException
from celery.utils.log import get_task_logger
from sqlalchemy import insert, select
from ..ontology.models import time_series, time_series_dataset, dataset as dataset_table
from ..ontology.schema import TimeSeries, TimeSeriesDatasetInDB, Dataset
from ..jobs.service import update_job_status
from .schema import IntegrationJobResultInDB
from .models import integration_jobs_results
from ...database.service import execute, fetch_one
from .agent import DirectoryIntegrationDeps, directory_integration_agent
from ...redis import get_redis


logger = get_task_logger(__name__)


async def run_integration_agent(
        job_id: uuid.UUID,
        api_key: str,
        data_path: str,
        data_description: str,
        data_source: str) -> IntegrationJobResultInDB:

    redis_stream = get_redis()

    if data_source == "directory":
        integration_agent = directory_integration_agent
        deps = DirectoryIntegrationDeps(
            api_key=api_key,
            data_directory=Path(data_path),
            data_description=data_description,
            redis_stream=redis_stream
        )
    else:
        raise ValueError(
            "Invalid data source, currently only directory is supported")

    try:
        nodes = []
        async with integration_agent.iter("Restructure and integrate the data", deps=deps) as agent_run:

            async for node in agent_run:
                nodes.append(node)
                logger.info(f"Integration agent state: {node}")
                await redis_stream.xadd(str(job_id), {"agent_state": str(node)})

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

        await update_job_status(job_id, "completed")

    except Exception as e:
        logger.error(f"Error running integration agent: {e}")

        await update_job_status(job_id, "failed")

        for file in Path(data_path).glob("*"):
            file.unlink()

        Path(data_path).rmdir()

        raise e

    else:
        return agent_output


@shared_task
def run_integration_job(job_id: uuid.UUID, api_key: str, data_path: str, data_description: str, data_source: str):

    loop = asyncio.get_event_loop()
    loop.run_until_complete(run_integration_agent(
        job_id, api_key, data_path, data_description, data_source))


def validate_restructured_data(
        data: pd.DataFrame,
        metadata: pd.DataFrame,
        mapping_dict: dict,
        index_first_level: str,
        index_second_level: str | None
) -> tuple[pd.DataFrame, pd.DataFrame, dict]:

    if index_first_level not in data.columns:
        raise HTTPException(
            status_code=400,
            detail=f"Invalid data: First level index column '{index_first_level}' not found in DataFrame"
        )

    if index_second_level:
        if index_second_level not in data.columns:
            raise HTTPException(
                status_code=400,
                detail=f"Invalid data: Second level index column '{index_second_level}' not found in DataFrame!"
            )
        data = data.set_index([index_first_level, index_second_level])
    else:
        data = data.set_index(index_first_level)

    # Check for empty dataframes
    if data.empty:
        raise HTTPException(
            status_code=400,
            detail="Data is empty, please check your data and try again"
        )

    try:
        metadata = metadata.set_index(index_first_level)
    except Exception as e:
        raise HTTPException(
            status_code=400,
            detail=f"Invalid metadata or index, the first level index is not present in the metadata, Error: {e}"
        )

    first_level_indices_data = set(
        data.index.get_level_values(0).unique().tolist())
    first_level_indices_metadata = set(
        metadata.index.get_level_values(0).unique().tolist())

    len_metadata = len(first_level_indices_metadata)
    len_data = len(first_level_indices_data)
    len_intersection = len(
        first_level_indices_metadata.intersection(first_level_indices_data))

    if not len_metadata == len_data or not len_metadata == len_intersection:
        intersection_fraction = len_intersection / len_metadata

        if intersection_fraction == 0:
            raise HTTPException(
                status_code=400,
                detail="No overlap between metadata and data, are you sure you set the right index?"
            )

        raise HTTPException(
            status_code=400,
            detail=f"Metadata index does not match data index, {intersection_fraction} of metadata is present in data"
        )

    return data, metadata, mapping_dict


async def insert_base_dataset(
        name: str,
        description: str,
        user_id: uuid.UUID,
        dataset_id: uuid.UUID | None = None) -> uuid.UUID:
    """
    Insert a base dataset into the database.

    Args:
        name: The name of the dataset
        description: A description of the dataset
        user_id: The ID of the user who owns the dataset

    Returns:
        The ID of the created dataset
    """
    if dataset_id is None:
        dataset_id = uuid.uuid4()

    dataset_record = Dataset(
        id=dataset_id,
        name=name,
        description=description,
        user_id=user_id,
        created_at=datetime.now(),
        updated_at=datetime.now()
    )

    await execute(
        insert(dataset_table).values(dataset_record.model_dump()),
        commit_after=True
    )

    return dataset_id


async def insert_time_series_dataset(
        df: pd.DataFrame,
        dataset_id: uuid.UUID,
        index_first_level: str,
        index_second_level: str | None = None) -> None:
    """
    Insert a time series dataset and its associated time series into the database.

    Args:
        df: The DataFrame containing the time series data
        dataset_id: The ID of the parent dataset
        index_first_level: The name of the first level index column
        index_second_level: The name of the second level index column (if multi-series)
    """
    # Calculate dataset statistics
    is_multi_series = df.index.nlevels > 1
    unique_series = df.index.get_level_values(0).unique()

    if is_multi_series:
        series_counts = df.groupby(level=0).size()
        num_series = len(unique_series)
    else:
        series_counts = np.array([len(df.index)])
        num_series = 1

    # Create and store time series dataset
    time_series_dataset_record = TimeSeriesDatasetInDB(
        id=dataset_id,
        num_series=num_series,
        num_features=len(df.columns),
        avg_num_timestamps=int(series_counts.mean()),
        max_num_timestamps=int(series_counts.max()),
        min_num_timestamps=int(series_counts.min()),
        index_first_level=index_first_level,
        index_second_level=index_second_level
    )

    await execute(
        insert(time_series_dataset).values(
            time_series_dataset_record.model_dump()),
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
                original_id=str(original_id)
            )

            await execute(
                insert(time_series).values(time_series_record.model_dump()),
                commit_after=True
            )
    else:
        series_id = uuid.uuid4()
        time_series_record = TimeSeries(
            id=series_id,
            description="Time series data",
            features=list(df.columns),
            num_timestamps=len(df),
            num_features=len(df.columns),
            start_timestamp=df.index.min(),
            end_timestamp=df.index.max(),
            dataset_id=dataset_id,
            original_id=None
        )

        await execute(
            insert(time_series).values(time_series_record.model_dump()),
            commit_after=True
        )


async def insert_restructured_data_to_db(
        df: pd.DataFrame,
        data_description: str,
        dataset_name: str,
        data_modality: str,
        user_id: uuid.UUID,
        dataset_id: uuid.UUID | None = None
) -> uuid.UUID:

    if data_modality != "time_series":
        raise HTTPException(
            status_code=400,
            detail="Only time series data is supported at the moment"
        )

    # Insert base dataset
    dataset_id = await insert_base_dataset(
        name=dataset_name,
        description=data_description,
        user_id=user_id,
        dataset_id=dataset_id
    )

    # Insert time series dataset and associated time series
    await insert_time_series_dataset(
        df=df,
        dataset_id=dataset_id,
        index_first_level=df.index.names[0],
        index_second_level=df.index.names[1] if len(
            df.index.names) > 1 else None
    )

    return dataset_id


async def get_job_results(job_id: uuid.UUID) -> IntegrationJobResultInDB:
    # get results from integration_jobs_results
    results = await fetch_one(
        select(integration_jobs_results).where(
            integration_jobs_results.c.job_id == job_id),
        commit_after=True
    )

    return IntegrationJobResultInDB(**results)
