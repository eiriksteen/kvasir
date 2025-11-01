import uuid
from datetime import datetime
from typing import List, Optional, Dict, Any, Union, Literal, Type, Tuple
from pydantic import BaseModel


from .data_sources import DataSource
from .pipeline import Pipeline


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


class ObjectGroupFromDataSourceInDB(BaseModel):
    data_source_id: uuid.UUID
    object_group_id: uuid.UUID


class ObjectGroupFromPipelineInDB(BaseModel):
    pipeline_id: uuid.UUID
    object_group_id: uuid.UUID
    pipeline_run_id: Optional[uuid.UUID] = None


# Schemas for the API


class DataObject(DataObjectInDB):
    modality_fields: Union[TimeSeriesInDB]


class ObjectGroupSources(BaseModel):
    data_sources: List[DataSource]
    pipelines: List[Pipeline]


class ObjectGroup(ObjectGroupInDB):
    modality_fields: Union[TimeSeriesGroupInDB]
    sources: ObjectGroupSources


# Derive from object groups in dataset (for ERD viz)
class DatasetSources(BaseModel):
    data_source_ids: List[uuid.UUID]
    pipeline_ids: List[uuid.UUID]


class Dataset(DatasetInDB):
    object_groups: List[ObjectGroup]
    sources: DatasetSources
    description_for_agent: str


class ObjectGroupWithObjects(ObjectGroup):
    objects: List[DataObject]


class GetDatasetsByIDsRequest(BaseModel):
    dataset_ids: List[uuid.UUID]


# Create schemas


class TimeSeriesCreate(BaseModel):
    original_id: str
    start_timestamp: datetime
    end_timestamp: datetime
    num_timestamps: int
    sampling_frequency: Literal["m", "h", "d", "w", "y", "irr"]
    timezone: str
    features_schema: Dict[str, Any]


class TimeSeriesGroupCreate(BaseModel):
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
    original_id: str
    description: Optional[str] = None
    modality_fields: Union[TimeSeriesCreate]

    class Config:
        extra = "allow"


class ObjectsFile(BaseModel):
    filename: str
    modality: MODALITY_LITERAL


class DataObjectGroupCreate(BaseModel):
    name: str
    original_id_name: str
    description: str
    modality: str
    # data source ids for groups coming directly from (files etc)
    data_source_ids: List[uuid.UUID]
    # pipeline ids for groups coming from in-memory, i.e pipelines applied to sources, but without saving the outputs permanently
    pipeline_ids: List[uuid.UUID]
    modality_fields: Union[TimeSeriesGroupCreate]
    objects_files: List[ObjectsFile] = []  # Objects that belong to this group

    # For custom fields decided by the agent to be interesting enough to be added
    class Config:
        extra = "allow"


class DatasetCreate(BaseModel):
    name: str
    description: str
    # TODO: Add more modalities
    groups: List[DataObjectGroupCreate] = []

    class Config:
        extra = "allow"


# Raw data schemas

class TimeSeriesWithRawData(DataObject):
    data: Dict[str, List[Tuple[datetime, Union[float, int]]]]


# Helpers
# Used to let the agent know the schemas it's dataframes must abide by

class DataObjectsInDBInfo(BaseModel):
    child_model: Type[BaseModel]
    parent_model: Type[BaseModel]
    create_model: Type[BaseModel]
    child_table_name: str
    parent_table_name: str


def get_data_objects_in_db_info(modality: MODALITY_LITERAL, type: Literal["object_group", "data_object"]) -> DataObjectsInDBInfo:
    if modality == "time_series":
        if type == "object_group":
            return DataObjectsInDBInfo(
                child_model=TimeSeriesGroupInDB,
                parent_model=ObjectGroupInDB,
                create_model=TimeSeriesGroupCreate,
                child_table_name="time_series_group",
                parent_table_name="object_group"
            )
        elif type == "data_object":
            return DataObjectsInDBInfo(
                child_model=TimeSeriesInDB,
                parent_model=DataObjectInDB,
                create_model=TimeSeriesCreate,
                child_table_name="time_series",
                parent_table_name="data_object"
            )
    else:
        raise ValueError(f"Invalid modality: {modality}")
