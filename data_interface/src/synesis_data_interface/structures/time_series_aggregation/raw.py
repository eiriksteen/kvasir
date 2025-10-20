import pandas as pd
from dataclasses import dataclass

from synesis_data_interface.structures.base.raw import MetadataStructure


@dataclass(kw_only=True)
class TimeSeriesAggregationMetadataStructure(MetadataStructure):
    time_series_aggregation_inputs: pd.DataFrame


@dataclass(kw_only=True)
class TimeSeriesAggregationStructure(TimeSeriesAggregationMetadataStructure):
    time_series_aggregation_outputs: pd.DataFrame
