import uuid
from datetime import datetime
from typing import List, Optional, Dict, Any, Union, Literal, Type, Tuple
from pydantic import BaseModel


# DB Schemas

MODALITY_LITERAL = Literal["time_series", "tabular"]


class DatasetBase(BaseModel):
    id: uuid.UUID
    user_id: uuid.UUID
    name: str
    description: str
    additional_variables: Optional[Dict[str, Any]] = None
    created_at: datetime
    updated_at: datetime


class DataObjectBase(BaseModel):
    id: uuid.UUID
    name: str
    group_id: uuid.UUID
    original_id: str
    description: Optional[str] = None
    additional_variables: Optional[Dict[str, Any]] = None
    created_at: datetime
    updated_at: datetime


class ObjectGroupBase(BaseModel):
    id: uuid.UUID
    name: str
    description: str
    modality: MODALITY_LITERAL
    dataset_id: uuid.UUID
    original_id_name: Optional[str] = None
    additional_variables: Optional[Dict[str, Any]] = None
    echart_id: Optional[uuid.UUID] = None
    created_at: datetime
    updated_at: datetime


class TimeSeriesBase(BaseModel):
    id: uuid.UUID  # Foreign key to data_object.id
    start_timestamp: datetime
    end_timestamp: datetime
    num_timestamps: int
    sampling_frequency: Literal["m", "h", "d", "w", "y", "irr"]
    timezone: Optional[str] = None
    features_schema: Dict[str, Any]
    created_at: datetime
    updated_at: datetime


class TimeSeriesGroupBase(BaseModel):
    id: uuid.UUID
    total_timestamps: int
    number_of_series: int
    # None if varying between series
    sampling_frequency: Optional[Literal["m",
                                         "h", "d", "w", "y", "irr"]] = None
    # None if varying between series
    timezone: Optional[str] = None
    # None if varying between series
    features_schema: Optional[Dict[str, Any]] = None
    earliest_timestamp: datetime
    latest_timestamp: datetime
    created_at: datetime
    updated_at: datetime


class TabularRowBase(BaseModel):
    id: uuid.UUID
    features_schema: Dict[str, Any]
    created_at: datetime
    updated_at: datetime


class TabularGroupBase(BaseModel):
    id: uuid.UUID
    number_of_entities: int
    number_of_features: int
    features_schema: Dict[str, Any]
    created_at: datetime
    updated_at: datetime


class DataObject(DataObjectBase):
    modality_fields: Union[TimeSeriesBase, TabularRowBase]


class ObjectGroup(ObjectGroupBase):
    modality_fields: Union[TimeSeriesGroupBase, TabularGroupBase]
    first_data_object: DataObject


class Dataset(DatasetBase):
    object_groups: List[ObjectGroup]


class ObjectGroupWithObjects(ObjectGroup):
    objects: List[DataObject]


# Create schemas


class DatasetBaseCreate(BaseModel):
    name: str
    description: Optional[str] = None


class TimeSeriesCreate(BaseModel):
    """
    Metadata for one time series object. Each DataFrame row represents one series.
    Compute all values from actual data - don't assume values.
    """
    start_timestamp: datetime
    end_timestamp: datetime
    num_timestamps: int
    sampling_frequency: Literal["m", "h", "d", "w", "y", "irr"]
    features_schema: Dict[str, Any]
    timezone: Optional[str] = None


class TimeSeriesGroupCreate(BaseModel):
    """
    Aggregated metadata computed from all time series in the group.
    Values are computed by aggregating across all series (e.g., earliest_timestamp = min of all start_timestamps).
    """
    total_timestamps: int
    number_of_series: int
    # None if varying between series
    sampling_frequency: Optional[Literal["m",
                                         "h", "d", "w", "y", "irr"]] = None
    # None if varying between series
    timezone: Optional[str] = None
    # None if varying between series
    features_schema: Optional[Dict[str, Any]] = None
    earliest_timestamp: datetime
    latest_timestamp: datetime


class TabularRowCreate(BaseModel):
    features_schema: Dict[str, Any]


class TabularGroupCreate(BaseModel):
    number_of_entities: int
    number_of_features: int
    features_schema: Dict[str, Any]


class DataObjectCreate(BaseModel):
    """
    Metadata for one data object. Each DataFrame row represents one object with its specific metadata.
    Compute all values from actual data - don't assume values.
    """
    name: str
    original_id: str
    description: Optional[str] = None
    modality_fields: Union[TimeSeriesCreate, TabularRowCreate]

    class Config:
        extra = "allow"


class ObjectsFile(BaseModel):
    filename: str
    modality: MODALITY_LITERAL


class ObjectGroupCreate(BaseModel):
    """
    Group of related data objects sharing the same modality.
    objects_files: Parquet files where each row represents one data object with its metadata.
    modality_fields: Aggregated statistics computed from all objects in the group.
    """
    name: str
    original_id_name: str
    dataset_id: uuid.UUID
    description: str
    modality: str
    modality_fields: Union[TimeSeriesGroupCreate, TabularGroupCreate]
    objects_files: List[ObjectsFile] = []  # Objects that belong to this group

    # For custom fields decided by the agent to be interesting enough to be added
    class Config:
        extra = "allow"


class DatasetCreate(BaseModel):
    """
    Complete dataset with object groups. Each group has:
    - Parquet files (objects_files) where each row = one data object with computed metadata
    - Aggregated group-level statistics (modality_fields)
    Compute all values from actual data - don't assume!
    """
    name: str
    description: str
    # TODO: Add more modalities
    groups: List[ObjectGroupCreate] = []

    class Config:
        extra = "allow"


# Update schemas
