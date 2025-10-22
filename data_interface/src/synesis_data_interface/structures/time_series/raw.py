import pandas as pd
from dataclasses import dataclass

from synesis_data_interface.structures.base.raw import MetadataStructure


@dataclass(kw_only=True)
class TimeSeriesStructure(MetadataStructure):
    time_series_data: pd.DataFrame
