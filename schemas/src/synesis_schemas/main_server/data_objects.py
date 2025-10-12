import uuid
from datetime import datetime
from typing import List, Optional, Dict, Any, Union, Literal, Tuple
from pydantic import BaseModel

from synesis_data_structures.base_schema import Feature, AggregationOutput


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
    group_id: Optional[uuid.UUID] = None
    original_id: Optional[str] = None
    description: Optional[str] = None
    additional_variables: Optional[Dict[str, Any]] = None
    created_at: datetime
    updated_at: datetime


class VariableInDB(BaseModel):
    id: uuid.UUID
    variable_group_id: uuid.UUID
    name: str
    description: str
    python_type: str
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


class VariableGroupFull(VariableGroupInDB):
    variables: List[VariableInDB]


class DatasetSources(BaseModel):
    data_source_ids: List[uuid.UUID]
    dataset_ids: List[uuid.UUID]
    pipeline_ids: List[uuid.UUID]


class DatasetFull(DatasetInDB):
    object_groups: List[ObjectGroupInDB]
    variable_groups: List[VariableGroupFull]
    sources: DatasetSources


class DatasetFullWithFeatures(DatasetInDB):
    object_groups: List[ObjectGroupWithFeatures]
    variable_groups: List[VariableGroupFull]
    sources: DatasetSources


class ObjectGroupWithEntitiesAndFeatures(ObjectGroupWithFeatures):
    objects: List[Union[TimeSeriesFull, TimeSeriesAggregationFull]]


class GetDatasetByIDsRequest(BaseModel):
    dataset_ids: List[uuid.UUID]
    include_features: bool = False


class AggregationObjectInDB(BaseModel):
    id: uuid.UUID
    name: str
    description: str
    created_at: datetime
    updated_at: datetime
    analysis_result_id: uuid.UUID | None = None # Foreign key to analysis_result.id 
    # Other variabels used to reference where the aggregation was created. This is so you can run a script to get the raw data.
    # For instance: in analysis result there is python code, this python code should be run to get the raw data. A serialization function is then applied to the raw data to get the final data structure.
    # automation_id: uuid.UUID | None = None # Foreign key to automation.id
    # script_path: str | None = None # The path to the script that defines the input and output of the aggregation


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


class VariableCreate(BaseModel):
    name: str
    python_type: str
    description: str


class VariableGroupCreate(BaseModel):
    name: str
    description: str
    save_path: str
    variables: List[VariableCreate]


class DatasetCreate(BaseModel):
    name: str
    description: str
    object_groups: List[ObjectGroupCreate]
    variable_groups: List[VariableGroupCreate]
    sources: DatasetSources


class AggregationObjectCreate(BaseModel):
    name: str
    description: str
    analysis_result_id: uuid.UUID | None = None # Do not need dataset_ids or data_source_ids here because they are already in the analysis result

class AggregationObjectUpdate(BaseModel):
    name: str
    description: str
