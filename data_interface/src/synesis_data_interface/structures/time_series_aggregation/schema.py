import uuid
from datetime import datetime
from typing import List, Dict, Tuple, Union
from synesis_data_interface.structures.base.schema import DataObject


# For aggregating time series, for example the mean of a series or the total number of events across multiple series
class TimeSeriesAggregation(DataObject):
    # Input data is dict of (time_series_id, input_feature_name) -> (start_timestamp, end_timestamp)
    input_data: Dict[Tuple[uuid.UUID, str], Tuple[datetime, datetime]]
    # Output data is dict of output_feature_name -> list of values
    # Float for continuous features, int for discrete features
    output_data: Dict[str, List[Union[float, int]]]
