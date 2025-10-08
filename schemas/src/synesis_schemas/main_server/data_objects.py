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
    created_at: datetime
    updated_at: datetime


class DatasetFromDataSourceInDB(BaseModel):
    data_source_id: uuid.UUID
    dataset_id: uuid.UUID


class DatasetFromDatasetInDB(BaseModel):
    source_dataset_id: uuid.UUID
    dataset_id: uuid.UUID


class DatasetFromPipelineInDB(BaseModel):
    pipeline_id: uuid.UUID
    dataset_id: uuid.UUID


class DataObjectInDB(BaseModel):
    id: uuid.UUID
    name: str
    structure_type: str
    group_id: Optional[uuid.UUID] = None
    original_id: Optional[str] = None
    description: Optional[str] = None
    additional_variables: Optional[Dict[str, Any]] = None
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
    structure_type: str
    save_path: str
    created_at: datetime
    updated_at: datetime
    original_id_name: Optional[str] = None


class TimeSeriesObjectGroupInDB(BaseModel):
    id: uuid.UUID
    time_series_df_schema: str
    time_series_df_head: str
    entity_metadata_df_schema: str
    entity_metadata_df_head: str
    feature_information_df_schema: str
    feature_information_df_head: str
    created_at: datetime
    updated_at: datetime


class TimeSeriesAggregationObjectGroupInDB(BaseModel):
    id: uuid.UUID
    time_series_aggregation_outputs_df_schema: str
    time_series_aggregation_outputs_df_head: str
    time_series_aggregation_inputs_df_schema: str
    time_series_aggregation_inputs_df_head: str
    entity_metadata_df_schema: str
    entity_metadata_df_head: str
    feature_information_df_schema: str
    feature_information_df_head: str
    created_at: datetime
    updated_at: datetime


class VariableGroupInDB(BaseModel):
    id: uuid.UUID
    dataset_id: uuid.UUID
    name: str
    description: str
    save_path: str
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


class ObjectGroup(ObjectGroupInDB):
    structure_fields: Union[TimeSeriesObjectGroupInDB,
                            TimeSeriesAggregationObjectGroupInDB]
    features: List[FeatureWithSource]


class DataObject(DataObjectInDB):
    structure_fields: Union[TimeSeriesInDB, TimeSeriesAggregationInDB]


class DataObjectWithParentGroup(DataObject):
    object_group: ObjectGroup


class DatasetSources(BaseModel):
    data_source_ids: List[uuid.UUID]
    dataset_ids: List[uuid.UUID]
    pipeline_ids: List[uuid.UUID]


class Dataset(DatasetInDB):
    object_groups: List[ObjectGroup]
    variable_groups: List[VariableGroupInDB]
    sources: DatasetSources


class ObjectGroupWithObjects(ObjectGroup):
    objects: List[DataObject]


class GetDatasetByIDsRequest(BaseModel):
    dataset_ids: List[uuid.UUID]


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
    save_path: str
    metadata_dataframes: List[MetadataDataframe]


class TimeSeriesObjectGroupCreate(ObjectGroupCreate):
    time_series_df_schema: str
    time_series_df_head: str
    entity_metadata_df_schema: str
    entity_metadata_df_head: str
    feature_information_df_schema: str
    feature_information_df_head: str


class TimeSeriesAggregationObjectGroupCreate(ObjectGroupCreate):
    time_series_aggregation_outputs_df_schema: str
    time_series_aggregation_outputs_df_head: str
    time_series_aggregation_inputs_df_schema: str
    time_series_aggregation_inputs_df_head: str
    entity_metadata_df_schema: str
    entity_metadata_df_head: str
    feature_information_df_schema: str
    feature_information_df_head: str


class VariableGroupCreate(BaseModel):
    name: str
    description: str
    save_path: str
    data: Dict[str, Any]


class DatasetCreate(BaseModel):
    name: str
    description: str
    object_groups: List[Union[TimeSeriesObjectGroupCreate,
                              TimeSeriesAggregationObjectGroupCreate]]
    variable_groups: List[VariableGroupCreate]
    sources: DatasetSources
