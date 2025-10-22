from typing import Union

from synesis_data_interface.structures.time_series.raw import TimeSeriesStructure
from synesis_data_interface.structures.time_series_aggregation.raw import TimeSeriesAggregationStructure
from synesis_data_interface.structures.time_series.synthetic import (
    generate_synthetic_time_series_data,
    get_time_series_synthetic_description
)
from synesis_data_interface.structures.time_series_aggregation.synthetic import (
    generate_synthetic_time_series_aggregation_data,
    get_time_series_aggregation_synthetic_description
)


def generate_synthetic_data(first_level_id: str) -> Union[TimeSeriesStructure, TimeSeriesAggregationStructure]:
    """
    Generate synthetic data for the specified first level structure.

    This is a unified API that delegates to the specific submodule implementations.

    Args:
        first_level_id: The first level ID of the data structure ('time_series' or 'time_series_aggregation')

    Returns:
        A TimeSeriesStructure or TimeSeriesAggregationStructure instance
    """
    if first_level_id == "time_series":
        return generate_synthetic_time_series_data()
    elif first_level_id == "time_series_aggregation":
        return generate_synthetic_time_series_aggregation_data()
    else:
        raise ValueError(f"Unknown first level ID: {first_level_id}")


def get_synthetic_data_description(first_level_id: str) -> str:
    """
    Get the description of the synthetic data generated for a specific data structure.

    This is a unified API that delegates to the specific submodule implementations.

    Args:
        first_level_id: The first level ID ('time_series' or 'time_series_aggregation')

    Returns:
        A string description of the synthetic dataset structure and contents
    """
    if first_level_id == "time_series":
        return get_time_series_synthetic_description()
    elif first_level_id == "time_series_aggregation":
        return get_time_series_aggregation_synthetic_description()
    else:
        raise ValueError(f"Unknown first level ID: {first_level_id}")
