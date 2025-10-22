import uuid
from datetime import datetime
from typing import List, Optional, Dict, Any, Union, Literal
from pydantic import BaseModel

from synesis_data_interface.structures.aggregation.schema import AggregationOutput

# DB Schemas


class DatasetInDB(BaseModel):
    id: uuid.UUID
    user_id: uuid.UUID
    name: str
    description: str
    created_at: datetime
    updated_at: datetime


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
    entity_metadata_df_schema: Optional[str] = None
    entity_metadata_df_head: Optional[str] = None
    feature_information_df_schema: Optional[str] = None
    feature_information_df_head: Optional[str] = None
    created_at: datetime
    updated_at: datetime


class TimeSeriesAggregationObjectGroupInDB(BaseModel):
    id: uuid.UUID
    time_series_aggregation_outputs_df_schema: str
    time_series_aggregation_outputs_df_head: str
    time_series_aggregation_inputs_df_schema: str
    time_series_aggregation_inputs_df_head: str
    entity_metadata_df_schema: Optional[str] = None
    entity_metadata_df_head: Optional[str] = None
    feature_information_df_schema: Optional[str] = None
    feature_information_df_head: Optional[str] = None
    created_at: datetime
    updated_at: datetime


class VariableGroupInDB(BaseModel):
    id: uuid.UUID
    name: str
    group_schema: Dict[str, Any]
    dataset_id: uuid.UUID
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


class AggregationObjectInDB(BaseModel):
    id: uuid.UUID
    name: str
    description: str
    created_at: datetime
    updated_at: datetime
    analysis_result_id: uuid.UUID | None = None  # Foreign key to analysis_result.id
    # Other variabels used to reference where the aggregation was created. This is so you can run a script to get the raw data.
    # For instance: in analysis result there is python code, this python code should be run to get the raw data. A serialization function is then applied to the raw data to get the final data structure.
    # automation_id: uuid.UUID | None = None # Foreign key to automation.id
    # script_path: str | None = None # The path to the script that defines the input and output of the aggregation


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
    pipeline_ids: List[uuid.UUID]


class Dataset(DatasetInDB):
    object_groups: List[ObjectGroup]
    variable_groups: List[VariableGroupInDB]
    sources: DatasetSources
    description_for_agent: str


class ObjectGroupWithObjects(ObjectGroup):
    objects: List[DataObject]


class GetDatasetsByIDsRequest(BaseModel):
    dataset_ids: List[uuid.UUID]


class AggregationObjectWithRawData(AggregationObjectInDB):
    data: AggregationOutput


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
    entity_metadata_df_schema: Optional[str] = None
    entity_metadata_df_head: Optional[str] = None
    feature_information_df_schema: Optional[str] = None
    feature_information_df_head: Optional[str] = None


class TimeSeriesAggregationObjectGroupCreate(ObjectGroupCreate):
    time_series_aggregation_outputs_df_schema: str
    time_series_aggregation_outputs_df_head: str
    time_series_aggregation_inputs_df_schema: str
    time_series_aggregation_inputs_df_head: str
    entity_metadata_df_schema: Optional[str] = None
    entity_metadata_df_head: Optional[str] = None
    feature_information_df_schema: Optional[str] = None
    feature_information_df_head: Optional[str] = None


class VariableGroupCreate(BaseModel):
    name: str
    description: str
    save_path: str
    group_schema: Dict[str, Any]


class DatasetCreate(BaseModel):
    name: str
    description: str
    object_groups: List[Union[TimeSeriesObjectGroupCreate,
                              TimeSeriesAggregationObjectGroupCreate]]
    variable_groups: List[VariableGroupCreate]
    sources: DatasetSources


class AggregationObjectCreate(BaseModel):
    name: str
    description: str
    # Do not need dataset_ids or data_source_ids here because they are already in the analysis result
    analysis_result_id: uuid.UUID | None = None


class AggregationObjectUpdate(BaseModel):
    name: str
    description: str
