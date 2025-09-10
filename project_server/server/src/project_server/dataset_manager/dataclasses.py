import uuid
from datetime import datetime
from typing import List, Optional, Literal, Union
from dataclasses import dataclass

from synesis_data_structures.time_series.df_dataclasses import TimeSeriesStructure, TimeSeriesAggregationStructure


# API dataclasses

@dataclass
class DataframeCreateAPI:
    filename: str
    structure_type: str


@dataclass
class ObjectGroupCreateAPI:
    name: str
    entity_id_name: str
    description: str
    structure_type: str
    dataframes: List[DataframeCreateAPI]


@dataclass
class DatasetCreateAPI:
    name: str
    description: str
    modality: str
    primary_object_group: ObjectGroupCreateAPI
    annotated_object_groups: List[ObjectGroupCreateAPI]
    computed_object_groups: List[ObjectGroupCreateAPI]


@dataclass
class ObjectGroupAPI:
    id: uuid.UUID
    dataset_id: uuid.UUID
    name: str
    description: str
    original_id_name: Optional[str] = None
    role: Literal["primary", "annotated", "derived"]
    structure_type: str
    created_at: datetime
    updated_at: datetime


@dataclass
class DatasetWithObjectGroupsAPI:
    id: uuid.UUID
    user_id: uuid.UUID
    name: str
    description: str
    modality: str
    created_at: datetime
    updated_at: datetime
    primary_object_group: ObjectGroupAPI
    annotated_object_groups: List[ObjectGroupAPI]
    computed_object_groups: List[ObjectGroupAPI]


# Local dataclasses


@dataclass
class ObjectGroupCreate:
    name: str
    entity_id_name: str
    description: str
    structure_type: str
    structure: Union[TimeSeriesStructure, TimeSeriesAggregationStructure]


@dataclass
class DatasetCreate:
    name: str
    description: str
    modality: str
    primary_object_group: ObjectGroupCreate
    annotated_object_groups: List[ObjectGroupCreate]
    computed_object_groups: List[ObjectGroupCreate]


@dataclass
class ObjectGroupWithRawData(ObjectGroupAPI):
    structure: Union[TimeSeriesStructure, TimeSeriesAggregationStructure]


@dataclass
class DatasetWithRawData(DatasetWithObjectGroupsAPI):
    primary_object_group: ObjectGroupWithRawData
    annotated_object_groups: List[ObjectGroupWithRawData]
    computed_object_groups: List[ObjectGroupWithRawData]
