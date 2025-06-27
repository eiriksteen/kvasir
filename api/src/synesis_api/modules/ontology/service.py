import uuid
import aiofiles.os
import pandas as pd
import numpy as np
from typing import List
from datetime import datetime, timezone
from pathlib import Path
from aiofiles import open as aiofiles_open
from sqlalchemy import select, insert, delete
from fastapi import HTTPException
from synesis_api.modules.ontology.models import time_series_dataset, dataset, time_series, dataset_metadata
from synesis_api.modules.ontology.schema import (
    TimeSeriesDatasetInDB,
    Datasets,
    TimeSeries,
    Dataset,
    DatasetMetadata,
    TimeSeriesInheritedDataset
)
from synesis_api.modules.jobs.schema import JobMetadata
from synesis_api.modules.data_integration.service import get_job_results_from_dataset_id
from synesis_api.modules.data_integration.models import integration_jobs_results
from synesis_api.modules.jobs.models import jobs
from synesis_api.database.service import fetch_all, fetch_one, execute


async def get_time_series_dataset(dataset_id: uuid.UUID) -> TimeSeriesInheritedDataset:
    query = select(dataset, time_series_dataset).where(
        time_series_dataset.c.id == dataset_id
    ).join(
        time_series_dataset, dataset.c.id == time_series_dataset.c.id
    )

    dataset = await fetch_one(query)
    return TimeSeriesInheritedDataset(**dataset)


async def get_user_time_series_datasets(user_id: uuid.UUID) -> List[TimeSeriesInheritedDataset]:
    query = select(dataset, time_series_dataset).join(
        time_series_dataset, dataset.c.id == time_series_dataset.c.id
    ).where(dataset.c.user_id == user_id)

    datasets = await fetch_all(query)
    return [TimeSeriesInheritedDataset(**dataset) for dataset in datasets]


async def get_user_datasets(user_id: uuid.UUID, only_completed: bool = True, include_integration_jobs: bool = False) -> Datasets:
    time_series = await get_user_time_series_datasets(user_id)
    if only_completed:
        completed_ids_query = select(integration_jobs_results.c.dataset_id).join(
            jobs, jobs.c.id == integration_jobs_results.c.job_id
        ).where(jobs.c.status == "completed")
        completed_ids = await fetch_all(completed_ids_query)
        completed_ids = [row["dataset_id"] for row in completed_ids]
        time_series = [
            ts for ts in time_series if ts.id in completed_ids]
    if include_integration_jobs:
        # Get integration jobs for all user datasets
        integration_jobs_by_dataset = await get_integration_jobs_for_user_datasets(user_id)

        # Populate integration_jobs for each time series dataset
        for ts_dataset in time_series:
            dataset_jobs = integration_jobs_by_dataset.get(ts_dataset.id, [])
            ts_dataset.integration_jobs = [
                JobMetadata(**job) for job in dataset_jobs]

    return Datasets(time_series=time_series)


async def get_user_datasets_by_ids(user_id: uuid.UUID, dataset_ids: List[uuid.UUID] = [], include_integration_jobs: bool = False) -> Datasets:
    time_series_query = select(dataset, time_series_dataset).join(
        time_series_dataset, dataset.c.id == time_series_dataset.c.id
    ).where(
        dataset.c.user_id == user_id,
        dataset.c.id.in_(dataset_ids)
    )

    time_series_datasets = await fetch_all(time_series_query)
    time_series = [TimeSeriesInheritedDataset(
        **dataset) for dataset in time_series_datasets]

    if include_integration_jobs:
        # Get integration jobs for the specified datasets
        integration_jobs_by_dataset = await get_integration_jobs_for_user_datasets(user_id)

        # Populate integration_jobs for each time series dataset
        for ts_dataset in time_series:
            dataset_jobs = integration_jobs_by_dataset.get(ts_dataset.id, [])
            ts_dataset.integration_jobs = [
                JobMetadata(**job) for job in dataset_jobs]

    return Datasets(time_series=time_series)


async def get_user_time_series_dataset_by_id(dataset_id: uuid.UUID, user_id: uuid.UUID) -> TimeSeriesDatasetInDB:
    dataset = await fetch_one(
        select(time_series_dataset).where(
            time_series_dataset.c.user_id == user_id, time_series_dataset.c.id == dataset_id)
    )

    return TimeSeriesDatasetInDB(**dataset)


async def get_user_time_series_dataset(user_id: uuid.UUID, dataset_id: uuid.UUID, include_integration_jobs: bool = False) -> TimeSeriesInheritedDataset:
    query = select(dataset, time_series_dataset).join(
        time_series_dataset, dataset.c.id == time_series_dataset.c.id
    ).where(
        dataset.c.user_id == user_id,
        dataset.c.id == dataset_id
    )

    dataset = await fetch_one(query)
    time_series_dataset_obj = TimeSeriesInheritedDataset(**dataset)

    if include_integration_jobs:
        # Get integration jobs for this specific dataset
        integration_jobs_by_dataset = await get_integration_jobs_for_user_datasets(user_id)
        dataset_jobs = integration_jobs_by_dataset.get(dataset_id, [])
        time_series_dataset_obj.integration_jobs = [
            JobMetadata(**job) for job in dataset_jobs]

    return time_series_dataset_obj


async def get_time_series_in_dataset(dataset_id: uuid.UUID) -> List[TimeSeries]:
    query = select(time_series).where(
        time_series.c.dataset_id == dataset_id
    )

    series = await fetch_all(query)
    return [TimeSeries(**s) for s in series]


async def create_base_dataset(
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
        created_at=datetime.now(timezone.utc),
        updated_at=datetime.now(timezone.utc)
    )

    await execute(
        insert(dataset).values(dataset_record.model_dump()),
        commit_after=True
    )

    return dataset_id


async def create_dataset_metadata(
        dataset_id: uuid.UUID,
        column_names: List[str],
        column_types: List[str],
        num_columns: int
) -> None:

    dataset_metadata_record = DatasetMetadata(
        dataset_id=dataset_id,
        column_names=column_names,
        column_types=column_types,
        num_columns=num_columns
    )

    await execute(
        insert(dataset_metadata).values(dataset_metadata_record.model_dump()),
        commit_after=True
    )


async def create_time_series_dataset(
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
        features=list(df.columns),
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

    # Create and store time series in a single batch
    time_series_records = []
    if is_multi_series:
        for original_id in unique_series:
            series_data = df.loc[original_id]
            series_id = uuid.uuid4()
            time_series_records.append(TimeSeries(
                id=series_id,
                num_timestamps=len(series_data),
                start_timestamp=series_data.index.min(),
                end_timestamp=series_data.index.max(),
                dataset_id=dataset_id,
                original_id=str(original_id)
            ).model_dump())
    else:
        series_id = uuid.uuid4()
        time_series_records.append(TimeSeries(
            id=series_id,
            num_timestamps=len(df),
            start_timestamp=df.index.min(),
            end_timestamp=df.index.max(),
            dataset_id=dataset_id,
            original_id=None
        ).model_dump())

    if time_series_records:
        await execute(
            insert(time_series).values(time_series_records),
            commit_after=True
        )


async def create_dataset(
    dataset_df: pd.DataFrame,
    metadata_df: pd.DataFrame,
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

    if dataset_id is None:
        dataset_id = uuid.uuid4()

    save_path = Path.cwd() / "integrated_data" / f"{user_id}" / f"{dataset_id}"
    save_path.mkdir(parents=True, exist_ok=True)

    try:
        async with aiofiles_open(save_path / "dataset.csv", "wb") as out_file:
            await out_file.write(dataset_df.reset_index().to_csv(index=False).encode("utf-8"))
        async with aiofiles_open(save_path / "metadata.csv", "wb") as out_file:
            await out_file.write(metadata_df.reset_index().to_csv(index=False).encode("utf-8"))
    except OSError as e:
        raise HTTPException(
            status_code=500, detail=f"Failed to write output file: {str(e)}")

    # Insert base dataset
    await create_base_dataset(
        name=dataset_name,
        description=data_description,
        user_id=user_id,
        dataset_id=dataset_id
    )

    await create_dataset_metadata(
        dataset_id=dataset_id,
        column_names=metadata_df.columns.tolist(),
        column_types=[str(t) for t in metadata_df.dtypes.tolist()],
        num_columns=len(metadata_df.columns)
    )

    # Insert time series dataset and associated time series
    await create_time_series_dataset(
        df=dataset_df,
        dataset_id=dataset_id,
        index_first_level=dataset_df.index.names[0],
        index_second_level=dataset_df.index.names[1] if len(
            dataset_df.index.names) > 1 else None
    )

    return dataset_id


async def delete_dataset(dataset_id: uuid.UUID, user_id: uuid.UUID):

    # Currently only time series datasets are supported

    save_path = Path.cwd() / "integrated_data" / f"{user_id}" / f"{dataset_id}"

    if save_path.exists():
        for file in save_path.iterdir():
            await aiofiles.os.remove(file)
        save_path.rmdir()

    await execute(
        delete(time_series).where(time_series.c.dataset_id == dataset_id),
        commit_after=True
    )

    await execute(
        delete(dataset_metadata).where(
            dataset_metadata.c.dataset_id == dataset_id),
        commit_after=True
    )

    await execute(
        delete(time_series_dataset).where(
            time_series_dataset.c.id == dataset_id),
        commit_after=True
    )

    await execute(
        delete(dataset).where(dataset.c.id == dataset_id),
        commit_after=True
    )


async def get_integration_jobs_for_user_datasets(user_id: uuid.UUID) -> dict[uuid.UUID, List[dict]]:
    """
    Get all integration jobs for datasets owned by a user.

    Args:
        user_id: The ID of the user

    Returns:
        A dictionary mapping dataset_id to a list of job metadata dictionaries
    """
    query = select(
        integration_jobs_results.c.dataset_id,
        jobs.c.id,
        jobs.c.type,
        jobs.c.status,
        jobs.c.job_name,
        jobs.c.started_at,
        jobs.c.completed_at
    ).join(
        jobs, jobs.c.id == integration_jobs_results.c.job_id
    ).join(
        dataset, dataset.c.id == integration_jobs_results.c.dataset_id
    ).where(
        dataset.c.user_id == user_id
    )

    results = await fetch_all(query)

    # Group jobs by dataset_id
    jobs_by_dataset = {}
    for row in results:
        dataset_id = row["dataset_id"]
        if dataset_id not in jobs_by_dataset:
            jobs_by_dataset[dataset_id] = []

        jobs_by_dataset[dataset_id].append({
            "id": row["id"],
            "type": row["type"],
            "status": row["status"],
            "job_name": row["job_name"],
            "started_at": row["started_at"],
            "completed_at": row["completed_at"]
        })

    return jobs_by_dataset
