import uuid
from datetime import datetime
from typing import List, Optional, Literal, Union
from dataclasses import dataclass

from synesis_data_structures.time_series.df_dataclasses import TimeSeriesStructure, TimeSeriesAggregationStructure


@dataclass
class ObjectGroupCreateWithRawData:
    name: str
    entity_id_name: str
    description: str
    structure_type: str
    structure: Union[TimeSeriesStructure, TimeSeriesAggregationStructure]


@dataclass
class DatasetCreateWithRawData:
    name: str
    description: str
    modality: str
    primary_object_group: ObjectGroupCreateWithRawData
    annotated_object_groups: List[ObjectGroupCreateWithRawData]
    computed_object_groups: List[ObjectGroupCreateWithRawData]


@dataclass
class ObjectGroupWithRawData:
    id: uuid.UUID
    dataset_id: uuid.UUID
    name: str
    description: str
    role: Literal["primary", "annotated", "derived"]
    structure_type: str
    created_at: datetime
    updated_at: datetime
    structure: Union[TimeSeriesStructure, TimeSeriesAggregationStructure]
    original_id_name: Optional[str] = None


@dataclass
class DatasetWithRawData:
    id: uuid.UUID
    user_id: uuid.UUID
    name: str
    description: str
    modality: str
    created_at: datetime
    updated_at: datetime
    primary_object_group: ObjectGroupWithRawData
    annotated_object_groups: List[ObjectGroupWithRawData]
    computed_object_groups: List[ObjectGroupWithRawData]
