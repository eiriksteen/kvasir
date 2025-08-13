import uuid
from datetime import datetime
from typing import List, Optional, Dict, Any, Union, Literal, Tuple

from synesis_api.base_schema import BaseSchema
from synesis_api.secrets import MODALITY_TYPE

from synesis_data_structures.base_schema import Feature


# DB Schemas


class DatasetInDB(BaseSchema):
    id: uuid.UUID
    user_id: uuid.UUID
    name: str
    description: str
    modality: MODALITY_TYPE
    created_at: datetime
    updated_at: datetime


class DataObjectInDB(BaseSchema):
    id: uuid.UUID
    name: str
    group_id: Optional[uuid.UUID] = None
    original_id: Optional[str] = None
    description: Optional[str] = None
    additional_variables: Optional[Dict[str, Any]] = None
    created_at: datetime
    updated_at: datetime


class DerivedObjectSourceInDB(BaseSchema):
    id: uuid.UUID
    derived_object_id: uuid.UUID
    original_object_id: uuid.UUID
    created_at: datetime
    updated_at: datetime


class FeatureInDB(BaseSchema):
    name: str
    unit: str
    description: str
    type: Literal["numerical", "categorical"]
    subtype: Literal["continuous", "discrete"]
    scale: Literal["ratio", "interval", "ordinal", "nominal"]
    created_at: datetime
    updated_at: datetime


class FeatureInGroupInDB(BaseSchema):
    group_id: uuid.UUID
    feature_name: str
    source: Literal["data", "metadata"]
    category_id: Optional[int] = None
    created_at: datetime
    updated_at: datetime


class FeatureWithSource(FeatureInDB):
    source: Literal["data", "metadata"]


class ObjectGroupInDB(BaseSchema):
    id: uuid.UUID
    dataset_id: uuid.UUID  # Foreign key to dataset.id
    name: str
    description: str
    original_id_name: Optional[str] = None
    role: Literal["primary", "annotated", "derived"]
    structure_type: str
    created_at: datetime
    updated_at: datetime


class ObjectGroupWithFeatures(ObjectGroupInDB):
    features: List[FeatureWithSource]


class TimeSeriesInDB(BaseSchema):
    id: uuid.UUID  # Foreign key to data_object.id
    num_timestamps: int
    start_timestamp: datetime
    end_timestamp: datetime
    sampling_frequency: Literal["m", "h", "d", "w", "y", "irr"]
    timezone: str


class TimeSeriesFull(DataObjectInDB, TimeSeriesInDB):
    type: Literal["time_series"] = "time_series"


class TimeSeriesFullWithRawData(TimeSeriesFull):
    data: Dict[str, List[Tuple[datetime, Union[float, int]]]]
    features: Dict[str, Feature]


class TimeSeriesAggregationInDB(BaseSchema):
    id: uuid.UUID  # Foreign key to data_object.id
    is_multi_series_computation: bool


class TimeSeriesAggregationFull(DataObjectInDB, TimeSeriesAggregationInDB):
    type: Literal["time_series_aggregation"] = "time_series_aggregation"


class TimeSeriesAggregationFullWithRawData(TimeSeriesAggregationFull):
    input_data: Dict[Tuple[uuid.UUID, str], Tuple[datetime, datetime]]
    output_data: Dict[str, List[Union[float, int]]]
    features: Dict[str, Feature]


class TimeSeriesAggregationInputInDB(BaseSchema):
    id: uuid.UUID  # Foreign key to data_object.id
    time_series_id: uuid.UUID  # Foreign key to time_series.id
    aggregation_id: uuid.UUID  # Foreign key to time_series_aggregation.id
    input_feature_name: str  # Foreign key to feature.feature_name
    start_timestamp: datetime
    end_timestamp: datetime
    created_at: datetime
    updated_at: datetime


# Schemas for the API


class DatasetWithObjectGroups(DatasetInDB):
    primary_object_group: ObjectGroupWithFeatures
    annotated_object_groups: List[ObjectGroupWithFeatures]
    computed_object_groups: List[ObjectGroupWithFeatures]


class ObjectGroupWithObjectList(ObjectGroupWithFeatures):
    objects: List[Union[TimeSeriesFull, TimeSeriesAggregationFull]]


class ObjectGroupsWithListsInDataset(BaseSchema):
    dataset_id: uuid.UUID
    primary_object_group: ObjectGroupWithObjectList
    annotated_object_groups: List[ObjectGroupWithObjectList]
    computed_object_groups: List[ObjectGroupWithObjectList]


# Create schemas


class DataframeCreate(BaseSchema):
    filename: str
    structure_type: str


class ObjectGroupCreate(BaseSchema):
    name: str
    entity_id_name: str
    description: str
    structure_type: str
    dataframes: List[DataframeCreate]


class DatasetCreate(BaseSchema):
    name: str
    description: str
    modality: MODALITY_TYPE
    primary_object_group: ObjectGroupCreate
    annotated_object_groups: List[ObjectGroupCreate]
    derived_object_groups: List[ObjectGroupCreate]
