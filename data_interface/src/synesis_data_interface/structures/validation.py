from typing import Union

from synesis_data_interface.structures.time_series.raw import TimeSeriesStructure
from synesis_data_interface.structures.time_series_aggregation.raw import TimeSeriesAggregationStructure
from synesis_data_interface.structures.time_series.validation import validate_time_series_dataclass
from synesis_data_interface.structures.time_series_aggregation.validation import validate_time_series_aggregation_dataclass


def validate_object_group_structure(data_structure: Union[TimeSeriesStructure, TimeSeriesAggregationStructure]) -> None:
    """
    Validate a dataclass data structure.

    This is a unified API that delegates to the specific submodule implementations.

    Args:
        data_structure: A TimeSeriesStructure or TimeSeriesAggregationStructure instance

    Raises:
        ValueError: If the data structure validation fails
    """
    if isinstance(data_structure, TimeSeriesStructure):
        validate_time_series_dataclass(data_structure)
    elif isinstance(data_structure, TimeSeriesAggregationStructure):
        validate_time_series_aggregation_dataclass(data_structure)
    else:
        raise ValueError(
            f"Expected TimeSeriesStructure or TimeSeriesAggregationStructure, got {type(data_structure).__name__}")
