from pydantic import BaseModel, Field
from pydantic_ai import RunContext
from typing import List

from project_server.agents.extraction.deps import ExtractionDeps
from synesis_schemas.main_server import (
    DatasetCreate,
    DatasetInDB,
    ObjectGroupInDB,
    MODALITY_LITERAL,
    TimeSeriesGroupCreate,
    TimeSeriesGroupInDB,
    DataSourceCreate,
    DataSourceInDB,
    FileDataSourceCreate,
    FileDataSourceInDB
)


# data sources

async def submit_file_data_source(ctx: RunContext[ExtractionDeps], data_source_id: str, request: FileDataSourceCreate) -> FileDataSourceInDB:
    pass


# datasets

async def submit_dataset(ctx: RunContext[ExtractionDeps], dataset_id: str, request: DatasetCreate) -> DatasetInDB:
    pass


async def submit_time_series_group(
        ctx: RunContext[ExtractionDeps],
        dataset_id: str,
        request: TimeSeriesGroupCreate) -> TimeSeriesGroupInDB:
    pass
