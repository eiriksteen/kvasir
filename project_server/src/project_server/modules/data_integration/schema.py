from typing import List, Union
from pydantic import BaseModel

from synesis_data_structures.time_series.df_dataclasses import TimeSeriesStructure, TimeSeriesAggregationStructure


class PrimaryObjectGroupCreate(BaseModel):
    name: str
    description: str
    structure_type: str
    entity_id_name: str
    data: Union[TimeSeriesStructure, TimeSeriesAggregationStructure]


class AnnotatedObjectGroupCreate(BaseModel):
    name: str
    description: str
    structure_type: str
    entity_id_name: str
    data: Union[TimeSeriesStructure, TimeSeriesAggregationStructure]


class DerivedObjectGroupCreate(BaseModel):
    name: str
    description: str
    structure_type: str
    entity_id_name: str
    data: Union[TimeSeriesStructure, TimeSeriesAggregationStructure]


class DatasetCreate(BaseModel):
    name: str
    description: str
    modality: str
    primary_object_group: PrimaryObjectGroupCreate
    annotated_object_groups: List[AnnotatedObjectGroupCreate]
    derived_object_groups: List[DerivedObjectGroupCreate]
