import uuid
from datetime import datetime
from typing import List, Optional, Dict, Any, Union, Literal, Type, Tuple
from pydantic import BaseModel


# DB Schemas

MODALITY_LITERAL = Literal["time_series", "tabular"]


class DatasetInDB(BaseModel):
    id: uuid.UUID
    user_id: uuid.UUID
    name: str
    description: str
    additional_variables: Optional[Dict[str, Any]] = None
    created_at: datetime
    updated_at: datetime


class DataObjectInDB(BaseModel):
    id: uuid.UUID
    name: str
    group_id: uuid.UUID
    original_id: str
    description: Optional[str] = None
    additional_variables: Optional[Dict[str, Any]] = None
    created_at: datetime
    updated_at: datetime


class ObjectGroupInDB(BaseModel):
    id: uuid.UUID
    name: str
    description: str
    modality: MODALITY_LITERAL
    dataset_id: uuid.UUID
    original_id_name: Optional[str] = None
    additional_variables: Optional[Dict[str, Any]] = None
    raw_data_read_script_path: Optional[str] = None
    raw_data_read_function_name: Optional[str] = None
    created_at: datetime
    updated_at: datetime


class TimeSeriesInDB(BaseModel):
    id: uuid.UUID  # Foreign key to data_object.id
    start_timestamp: datetime
    end_timestamp: datetime
    num_timestamps: int
    sampling_frequency: Literal["m", "h", "d", "w", "y", "irr"]
    timezone: str
    features_schema: Dict[str, Any]
    created_at: datetime
    updated_at: datetime


class TimeSeriesGroupInDB(BaseModel):
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


# Raw data schemas


class TimeSeriesRawDataParams(BaseModel):
    """
    Parameters for reading raw data from a time series data object. 
    The start_timestamp and end_timestamp are the start and end timestamps of the data that has been read (not the full time series). 
    All params must be accepted as inputs to the function that reads the raw data. 
    The default values in the function should be the most recent 96 values of the time series. 
    """
    start_timestamp: datetime
    end_timestamp: datetime


class TimeSeriesRawData(BaseModel):
    """"
    Raw data for a time series data object, for display in the UI. 
    """
    data: Dict[str, List[Tuple[datetime, Union[float, int]]]]
    params: TimeSeriesRawDataParams


class DataObjectRawData(BaseModel):
    # TODO: Add more modalities
    original_id: str
    modality: MODALITY_LITERAL
    data: Union[TimeSeriesRawData]


# Schemas for the API


class DataObject(DataObjectInDB):
    modality_fields: Union[TimeSeriesInDB]


class ObjectGroup(ObjectGroupInDB):
    modality_fields: Union[TimeSeriesGroupInDB]
    first_data_object: DataObject


class Dataset(DatasetInDB):
    object_groups: List[ObjectGroup]


class ObjectGroupWithObjects(ObjectGroup):
    objects: List[DataObject]


class GetDatasetsByIDsRequest(BaseModel):
    dataset_ids: List[uuid.UUID]


class GetRawDataRequest(BaseModel):
    project_id: uuid.UUID
    object_id: uuid.UUID
    args: Union[TimeSeriesRawDataParams]


# Create schemas


class TimeSeriesCreate(BaseModel):
    """
    Metadata for one time series object. Each DataFrame row represents one series.
    Compute all values from actual data - don't assume values.
    """
    start_timestamp: datetime
    end_timestamp: datetime
    num_timestamps: int
    sampling_frequency: Literal["m", "h", "d", "w", "y", "irr"]
    timezone: str
    features_schema: Dict[str, Any]


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


class DataObjectCreate(BaseModel):
    """
    Metadata for one data object. Each DataFrame row represents one object with its specific metadata.
    Compute all values from actual data - don't assume values.
    """
    name: str
    original_id: str
    description: Optional[str] = None
    modality_fields: Union[TimeSeriesCreate]

    class Config:
        extra = "allow"


class ObjectsFile(BaseModel):
    filename: str
    modality: MODALITY_LITERAL


class DataObjectGroupCreate(BaseModel):
    """
    Group of related data objects sharing the same modality.
    objects_files: Parquet files where each row represents one data object with its metadata.
    modality_fields: Aggregated statistics computed from all objects in the group.
    """
    name: str
    original_id_name: str
    description: str
    modality: str
    modality_fields: Union[TimeSeriesGroupCreate]
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
    groups: List[DataObjectGroupCreate] = []

    class Config:
        extra = "allow"


# Update schemas

class UpdateObjectGroupRawDataScriptRequest(BaseModel):
    raw_data_read_script_path: str
    raw_data_read_function_name: str

# Helpers
# Used to let the agent know the schemas it's dataframes must abide by


class ModalityModels(BaseModel):
    child_model: Type[BaseModel]
    child_table_name: str


def get_modality_models(modality: MODALITY_LITERAL, type: Literal["object_group", "data_object"]) -> ModalityModels:
    if modality == "time_series":
        if type == "object_group":
            return ModalityModels(
                child_model=TimeSeriesGroupInDB,
                child_table_name="time_series_group"
            )
        elif type == "data_object":
            return ModalityModels(
                child_model=TimeSeriesInDB,
                child_table_name="time_series"
            )
        else:
            raise ValueError(f"Invalid type: {type}")
    else:
        raise ValueError(f"Invalid modality: {modality}")
