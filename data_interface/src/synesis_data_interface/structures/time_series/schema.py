from datetime import datetime
from typing import List, Dict, Tuple, Union
from synesis_data_interface.structures.base.schema import DataObject


class TimeSeries(DataObject):
    # Data is feature_name -> list of (timestamp, value)
    # Float for continuous features, int for discrete features
    data: Dict[str, List[Tuple[datetime, Union[float, int]]]]
