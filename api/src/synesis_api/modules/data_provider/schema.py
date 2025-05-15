import uuid
from datetime import datetime, timezone
from typing import List
from synesis_api.base_schema import BaseSchema


class TimeSeriesData(BaseSchema):
    id: uuid.UUID
    timestamps: List[datetime]
    values: List[List[float]]
    feature_names: List[str]
    missing_values: List[List[bool]]
