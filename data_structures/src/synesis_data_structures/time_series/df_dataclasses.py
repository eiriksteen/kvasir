import pandas as pd
from dataclasses import dataclass
from typing import Optional


@dataclass
class TimeSeriesStructure:
    time_series_data: pd.DataFrame
    time_series_entity_metadata: Optional[pd.DataFrame] = None
    feature_information: Optional[pd.DataFrame] = None


@dataclass
class TimeSeriesAggregationStructure:
    time_series_aggregation_outputs: pd.DataFrame
    time_series_aggregation_inputs: pd.DataFrame
    time_series_aggregation_metadata: Optional[pd.DataFrame] = None
    feature_information: Optional[pd.DataFrame] = None
