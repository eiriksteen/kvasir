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
    data: Union[TimeSeriesStructure, TimeSeriesAggregationStructure]


@dataclass
class TimeSeriesObjectGroupCreateWithRawData(ObjectGroupCreateWithRawData):
    time_series_df_schema: str
    time_series_df_head: str
    entity_metadata_df_schema: str
    entity_metadata_df_head: str
    feature_information_df_schema: str
    feature_information_df_head: str


@dataclass
class TimeSeriesAggregationObjectGroupCreateWithRawData(ObjectGroupCreateWithRawData):
    time_series_aggregation_outputs_df_schema: str
    time_series_aggregation_outputs_df_head: str
    time_series_aggregation_inputs_df_schema: str
    time_series_aggregation_inputs_df_head: str
    entity_metadata_df_schema: str
    entity_metadata_df_head: str
    feature_information_df_schema: str
    feature_information_df_head: str


@dataclass
class VariableGroupCreateWithRawData:
    name: str
    description: str
    data: Dict[str, Any] | object


@dataclass
class DatasetCreateWithRawData:
    name: str
    description: str
    object_groups: List[ObjectGroupCreateWithRawData]
    variable_groups: List[VariableGroupCreateWithRawData]


@dataclass
class DatasetCreateWithRawDataFull:
    name: str
    description: str
    object_groups: List[Union[TimeSeriesObjectGroupCreateWithRawData,
                              TimeSeriesAggregationObjectGroupCreateWithRawData]]
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
    data: Union[TimeSeriesStructure, TimeSeriesAggregationStructure]
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
    data: Dict[str, Any] | object


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
