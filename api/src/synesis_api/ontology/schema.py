import uuid
from datetime import datetime
from typing import List
from ..base_schema import BaseSchema


class DatasetBase(BaseSchema):
    id: uuid.UUID
    user_id: uuid.UUID
    name: str
    description: str
    created_at: datetime
    updated_at: datetime


class FeatureDataset(DatasetBase):
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


class TimeSeriesDataset(DatasetBase):
    num_series: int
    num_features: int
    avg_num_timestamps: int
    max_num_timestamps: int
    min_num_timestamps: int
    index_first_level: str
    index_second_level: str | None = None


class Datasets(BaseSchema):
    time_series: List[TimeSeriesDataset]
    # TODO: add documents, feature-based, images, etc
