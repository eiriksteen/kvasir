import pandas as pd
from dataclasses import dataclass
from typing import Optional, Union
from typing import List


# Separate metadata structures and raw data structures, since sometimes we want to access the metadata without loading the raw data
@dataclass
class MetadataStructure:
    entity_metadata: Optional[pd.DataFrame] = None
    feature_information: Optional[pd.DataFrame] = None


@dataclass
class TimeSeriesAggregationMetadataStructure(MetadataStructure):
    time_series_aggregation_inputs: pd.DataFrame


@dataclass
class TimeSeriesStructure(MetadataStructure):
    time_series_data: pd.DataFrame


@dataclass
class TimeSeriesAggregationStructure(TimeSeriesAggregationMetadataStructure):
    time_series_aggregation_outputs: pd.DataFrame
