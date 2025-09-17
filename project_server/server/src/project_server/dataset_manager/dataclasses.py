import uuid
from pathlib import Path
from datetime import datetime
from typing import List, Optional, Union, Dict, Any
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
class RawVariableCreate:
    name: str
    python_type: str
    description: str


@dataclass
class VariableGroupCreateWithRawData:
    name: str
    description: str
    variables: List[RawVariableCreate]
    data: Dict[str, Any]


@dataclass
class DatasetCreateWithRawData:
    name: str
    description: str
    object_groups: List[ObjectGroupCreateWithRawData]
    variable_groups: List[VariableGroupCreateWithRawData]


@dataclass
class ObjectGroupWithRawData:
    id: uuid.UUID
    dataset_id: uuid.UUID
    name: str
    description: str
    structure_type: str
    save_path: Path
    created_at: datetime
    updated_at: datetime
    structure: Union[TimeSeriesStructure, TimeSeriesAggregationStructure]
    original_id_name: Optional[str] = None


@dataclass
class DatasetVariable:
    id: uuid.UUID
    variable_group_id: uuid.UUID
    name: str
    python_type: str
    description: str
    created_at: datetime
    updated_at: datetime


@dataclass
class DatasetVariableGroupWithRawData:
    id: uuid.UUID
    dataset_id: uuid.UUID
    name: str
    description: str
    variables: List[DatasetVariable]
    data: Dict[str, Any]


@dataclass
class DatasetWithRawData:
    id: uuid.UUID
    user_id: uuid.UUID
    name: str
    description: str
    created_at: datetime
    updated_at: datetime
    object_groups: List[ObjectGroupWithRawData]
    variable_groups: List[DatasetVariableGroupWithRawData]
