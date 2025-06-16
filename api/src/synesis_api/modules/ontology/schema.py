import uuid
from datetime import datetime, timezone
from typing import List
from synesis_api.base_schema import BaseSchema


class Dataset(BaseSchema):
    job_id: uuid.UUID
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


class FeatureDatasetInDB(BaseSchema):
    id: uuid.UUID
    features: List[str]
    num_features: int


class FeatureDataset(Dataset):
    features: List[str]
    num_features: int


class TimeSeries(BaseSchema):
    id: uuid.UUID
    dataset_id: uuid.UUID
    original_id: str | None
    description: str
    features: List[str]
    num_timestamps: int
    num_features: int
    start_timestamp: datetime
    end_timestamp: datetime


class TimeSeriesDatasetInDB(BaseSchema):
    id: uuid.UUID
    num_series: int
    num_features: int
    avg_num_timestamps: int
    max_num_timestamps: int
    min_num_timestamps: int
    index_first_level: str
    index_second_level: str | None = None


class TimeSeriesDataset(Dataset):
    id: uuid.UUID
    num_series: int
    num_features: int
    avg_num_timestamps: int
    max_num_timestamps: int
    min_num_timestamps: int
    index_first_level: str
    index_second_level: str | None = None


class Datasets(BaseSchema):
    time_series: List[TimeSeriesDataset] = []
    tabular: List[FeatureDataset] = []
    num_datasets: int = 0
    # TODO: add documents, feature-based, images, etc
