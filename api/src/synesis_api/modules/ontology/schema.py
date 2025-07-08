import uuid
from datetime import datetime, timezone
from typing import List
from synesis_api.base_schema import BaseSchema
from synesis_api.modules.jobs.schema import JobMetadata


class Dataset(BaseSchema):
    id: uuid.UUID
    user_id: uuid.UUID
    name: str
    description: str
    created_at: datetime = datetime.now(timezone.utc)
    updated_at: datetime = datetime.now(timezone.utc)


class DatasetMetadata(BaseSchema):
    dataset_id: uuid.UUID
    num_columns: int
    column_names: List[str]
    column_types: List[str]


class TabularDatasetInDB(BaseSchema):
    id: uuid.UUID
    features: List[str]
    num_features: int


class TabularInheritedDataset(Dataset, TabularDatasetInDB):
    integration_jobs: List[JobMetadata] | None = None


class TimeSeries(BaseSchema):
    id: uuid.UUID
    dataset_id: uuid.UUID
    original_id: str | None
    num_timestamps: int
    start_timestamp: datetime
    end_timestamp: datetime


class TimeSeriesDatasetInDB(BaseSchema):
    id: uuid.UUID
    num_series: int
    num_features: int
    features: List[str]
    avg_num_timestamps: int
    max_num_timestamps: int
    min_num_timestamps: int
    index_first_level: str
    index_second_level: str | None = None


class TimeSeriesInheritedDataset(Dataset, TimeSeriesDatasetInDB):
    integration_jobs: List[JobMetadata] | None = None


class Datasets(BaseSchema):
    time_series: List[TimeSeriesInheritedDataset] = []
    tabular: List[TabularInheritedDataset] = []
    # TODO: add documents, feature-based, images, etc
