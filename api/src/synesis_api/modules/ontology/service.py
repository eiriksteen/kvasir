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
    TimeSeriesDataset,
    Datasets,
    TimeSeries,
    Dataset,
    TimeSeriesDatasetInDB,
    DatasetMetadata
)
from synesis_api.modules.integration.models import integration_jobs_results
from synesis_api.modules.jobs.models import jobs
from synesis_api.database.service import fetch_all, fetch_one, execute


async def get_user_time_series_datasets(user_id: uuid.UUID) -> List[TimeSeriesDataset]:
    query = select(dataset, time_series_dataset).join(
        time_series_dataset, dataset.c.job_id == time_series_dataset.c.id
    ).where(dataset.c.user_id == user_id)

    datasets = await fetch_all(query)
    return [TimeSeriesDataset(**dataset) for dataset in datasets]


async def get_user_datasets(user_id: uuid.UUID, only_completed: bool = True) -> Datasets:
    time_series = await get_user_time_series_datasets(user_id)
    if only_completed:
        completed_ids_query = select(integration_jobs_results.c.dataset_id).join(
            jobs, jobs.c.id == integration_jobs_results.c.job_id
        ).where(jobs.c.status == "completed")
        completed_ids = await fetch_all(completed_ids_query)
        completed_ids = [row["dataset_id"] for row in completed_ids]
        time_series = [
            ts for ts in time_series if ts.id in completed_ids]
    return Datasets(time_series=time_series)


async def get_user_datasets_by_ids(user_id: uuid.UUID, dataset_ids: List[uuid.UUID] = []) -> Datasets:
    time_series_query = select(dataset, time_series_dataset).join(
        time_series_dataset, dataset.c.job_id == time_series_dataset.c.id
    ).where(
        dataset.c.user_id == user_id,
        dataset.c.job_id.in_(dataset_ids)
    )

    time_series_datasets = await fetch_all(time_series_query)
    return Datasets(time_series=[TimeSeriesDataset(**dataset) for dataset in time_series_datasets])

async def get_user_time_series_dataset_by_id(dataset_id: uuid.UUID, user_id: uuid.UUID) -> TimeSeriesDataset:
    dataset = await fetch_one(
        select(time_series_dataset).where(
            time_series_dataset.c.user_id == user_id, time_series_dataset.c.id == dataset_id)
    )

    return TimeSeriesDataset(**dataset)


async def get_user_time_series_dataset(user_id: uuid.UUID, dataset_id: uuid.UUID) -> TimeSeriesDataset:
    query = select(dataset, time_series_dataset).join(
        time_series_dataset, dataset.c.job_id == time_series_dataset.c.id
    ).where(
        dataset.c.user_id == user_id,
        dataset.c.id == dataset_id
    )

    dataset = await fetch_one(query)
    return TimeSeriesDataset(**dataset)


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
        job_id=dataset_id,
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
                description=f"Time series {series_id}",
                features=list(df.columns),
                num_timestamps=len(series_data),
                num_features=len(df.columns),
                start_timestamp=series_data.index.min(),
                end_timestamp=series_data.index.max(),
                dataset_id=dataset_id,
                original_id=str(original_id)
            ).model_dump())
    else:
        series_id = uuid.uuid4()
        time_series_records.append(TimeSeries(
            id=series_id,
            description="Time series data",
            features=list(df.columns),
            num_timestamps=len(df),
            num_features=len(df.columns),
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
