import uuid
from datetime import datetime
from typing import List, Optional
from ..base_schema import BaseSchema


class TimeSeries(BaseSchema):
    id: uuid.UUID
    description: str
    features: List[str]
    num_timestamps: int
    num_features: int
    start_timestamp: datetime
    end_timestamp: datetime
    dataset_id: uuid.UUID
    original_id: Optional[str]
    created_at: datetime
    updated_at: datetime


class TimeSeriesDataset(BaseSchema):
    id: uuid.UUID
    user_id: uuid.UUID
    name: str
    description: str
    num_series: int
    num_features: int
    avg_num_timestamps: int
    max_num_timestamps: int
    min_num_timestamps: int
    index_first_level: str
    index_second_level: str | None = None
    created_at: datetime
    updated_at: datetime
