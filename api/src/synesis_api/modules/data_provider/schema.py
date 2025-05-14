import uuid
from datetime import datetime
from typing import List
from synesis_api.base_schema import BaseSchema


class TimeSeriesData(BaseSchema):
    id: uuid.UUID
    original_id: str
    timestamps: List[datetime]
    values: List[List[float | None]]
    feature_names: List[str]


class EntityMetadata(BaseSchema):
    dataset_id: uuid.UUID
    entity_id: uuid.UUID
    original_id: str
    original_id_name: str
    column_names: List[str]
    column_types: List[str]
    values: List[str | int | float | bool | None]


class TimeSeriesDataWithMetadata(TimeSeriesData):
    metadata: EntityMetadata
