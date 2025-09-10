import uuid
from datetime import datetime
from typing import List, Optional, Dict, Any, Union, Literal, Tuple
from pydantic import BaseModel

from synesis_data_structures.base_schema import Feature


# DB Schemas


class DatasetInDB(BaseModel):
    id: uuid.UUID
    user_id: uuid.UUID
    name: str
    description: str
    modality: Literal["time_series", "document",
                      "image", "video", "multimodal"]
    created_at: datetime
    updated_at: datetime


class DataObjectInDB(BaseModel):
    id: uuid.UUID
    name: str
    group_id: Optional[uuid.UUID] = None
    original_id: Optional[str] = None
    description: Optional[str] = None
    additional_variables: Optional[Dict[str, Any]] = None
    created_at: datetime
    updated_at: datetime


class DerivedObjectSourceInDB(BaseModel):
    id: uuid.UUID
    derived_object_id: uuid.UUID
    original_object_id: uuid.UUID
    created_at: datetime
    updated_at: datetime


class FeatureInDB(BaseModel):
    name: str
    description: str
    type: Literal["numerical", "categorical"]
    subtype: Literal["continuous", "discrete"]
    scale: Literal["ratio", "interval", "ordinal", "nominal"]
    created_at: datetime
    updated_at: datetime
    unit: Optional[str] = None


class FeatureInGroupInDB(BaseModel):
    group_id: uuid.UUID
    feature_name: str
    source: Literal["data", "metadata"]
    category_id: Optional[int] = None
    created_at: datetime
    updated_at: datetime


class ObjectGroupInDB(BaseModel):
    id: uuid.UUID
    dataset_id: uuid.UUID  # Foreign key to dataset.id
    name: str
    description: str
    original_id_name: Optional[str] = None
    role: Literal["primary", "annotated", "derived"]
    structure_type: str
    created_at: datetime
    updated_at: datetime


class TimeSeriesInDB(BaseModel):
    id: uuid.UUID  # Foreign key to data_object.id
    num_timestamps: int
    start_timestamp: datetime
    end_timestamp: datetime
    sampling_frequency: Literal["m", "h", "d", "w", "y", "irr"]
    timezone: str


class TimeSeriesAggregationInDB(BaseModel):
    id: uuid.UUID  # Foreign key to data_object.id
    is_multi_series_computation: bool


class TimeSeriesAggregationInputInDB(BaseModel):
    id: uuid.UUID  # Foreign key to data_object.id
    time_series_id: uuid.UUID  # Foreign key to time_series.id
    aggregation_id: uuid.UUID  # Foreign key to time_series_aggregation.id
    input_feature_name: str  # Foreign key to feature.feature_name
    start_timestamp: datetime
    end_timestamp: datetime
    created_at: datetime
    updated_at: datetime


# Schemas for the API


class FeatureWithSource(FeatureInDB):
    source: Literal["data", "metadata"]


class ObjectGroupWithFeatures(ObjectGroupInDB):
    features: List[FeatureWithSource]


class TimeSeriesFull(DataObjectInDB, TimeSeriesInDB):
    type: Literal["time_series"] = "time_series"


class TimeSeriesFullWithRawData(TimeSeriesFull):
    data: Dict[str, List[Tuple[datetime, Union[float, int]]]]
    features: Dict[str, Feature]


class TimeSeriesAggregationFull(DataObjectInDB, TimeSeriesAggregationInDB):
    type: Literal["time_series_aggregation"] = "time_series_aggregation"


class TimeSeriesAggregationFullWithRawData(TimeSeriesAggregationFull):
    input_data: Dict[Tuple[uuid.UUID, str], Tuple[datetime, datetime]]
    output_data: Dict[str, List[Union[float, int]]]
    features: Dict[str, Feature]


class DatasetWithObjectGroups(DatasetInDB):
    primary_object_group: ObjectGroupInDB
    annotated_object_groups: List[ObjectGroupInDB]
    computed_object_groups: List[ObjectGroupInDB]


class DatasetWithObjectGroupsAndFeatures(DatasetInDB):
    primary_object_group: ObjectGroupWithFeatures
    annotated_object_groups: List[ObjectGroupWithFeatures]
    computed_object_groups: List[ObjectGroupWithFeatures]


class ObjectGroupWithEntitiesAndFeatures(ObjectGroupWithFeatures):
    objects: List[Union[TimeSeriesFull, TimeSeriesAggregationFull]]


class ObjectGroupsWithEntitiesAndFeaturesInDataset(BaseModel):
    dataset_id: uuid.UUID
    primary_object_group: ObjectGroupWithEntitiesAndFeatures
    annotated_object_groups: List[ObjectGroupWithEntitiesAndFeatures]
    computed_object_groups: List[ObjectGroupWithEntitiesAndFeatures]


# Create schemas


class FeatureCreate(BaseModel):
    name: str
    description: str
    type: Literal["numerical", "categorical"]
    subtype: Literal["continuous", "discrete"]
    scale: Literal["ratio", "interval", "ordinal", "nominal"]
    unit: Optional[str] = None


class MetadataDataframe(BaseModel):
    filename: str
    second_level_id: str


class ObjectGroupCreate(BaseModel):
    name: str
    entity_id_name: str
    description: str
    structure_type: str
    metadata_dataframes: List[MetadataDataframe]


class DatasetCreate(BaseModel):
    name: str
    description: str
    modality: Literal["time_series", "document",
                      "image", "video", "multimodal"]
    primary_object_group: ObjectGroupCreate
    annotated_object_groups: List[ObjectGroupCreate]
    computed_object_groups: List[ObjectGroupCreate]
