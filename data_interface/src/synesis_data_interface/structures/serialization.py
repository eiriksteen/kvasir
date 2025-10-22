from typing import List, Union, Dict

from synesis_data_interface.structures.time_series.schema import TimeSeries
from synesis_data_interface.structures.time_series_aggregation.schema import TimeSeriesAggregation
from synesis_data_interface.structures.time_series.raw import TimeSeriesStructure
from synesis_data_interface.structures.time_series_aggregation.raw import (
    TimeSeriesAggregationStructure,
    TimeSeriesAggregationMetadataStructure
)
from synesis_data_interface.structures.base.raw import MetadataStructure
from synesis_data_interface.structures.time_series.serialization import (
    serialize_time_series_dataclass_to_api_payload,
    serialize_dataframes_to_parquet as serialize_time_series_to_parquet,
    deserialize_parquet_to_dataframes as deserialize_time_series_from_parquet
)
from synesis_data_interface.structures.time_series_aggregation.serialization import (
    serialize_time_series_aggregation_structure_to_api_payloads,
    serialize_dataframes_to_parquet as serialize_time_series_aggregation_to_parquet,
    deserialize_parquet_to_dataframes as deserialize_time_series_aggregation_from_parquet
)


def serialize_dataframes_to_api_payloads(data_structure: Union[TimeSeriesStructure, TimeSeriesAggregationStructure]) -> List[Union[TimeSeries, TimeSeriesAggregation]]:
    """
    Serialize a dataclass data structure to API payload objects for sending to client.

    This is a unified API that delegates to the specific submodule implementations.

    Args:
        data_structure: A TimeSeriesStructure or TimeSeriesAggregationStructure instance

    Returns:
        List of API payload objects (TimeSeries or TimeSeriesAggregation)
    """

    if isinstance(data_structure, TimeSeriesStructure):
        return serialize_time_series_dataclass_to_api_payload(data_structure)
    elif isinstance(data_structure, TimeSeriesAggregationStructure):
        return serialize_time_series_aggregation_structure_to_api_payloads(data_structure)
    else:
        raise ValueError(
            f"Expected TimeSeriesStructure or TimeSeriesAggregationStructure, got {type(data_structure).__name__}")


def serialize_dataframes_to_parquet(data_structure: Union[TimeSeriesStructure, TimeSeriesAggregationStructure]) -> Dict[str, bytes]:
    """
    Serialize a dataclass data structure to parquet format for processing unit.

    This function takes the DataFrames and returns them as bytes ready for direct HTTP submission.
    The output is a dictionary with second_level_id as key and the corresponding parquet bytes as value.

    This is a unified API that delegates to the specific submodule implementations.

    Args:
        data_structure: A TimeSeriesStructure or TimeSeriesAggregationStructure instance

    Returns:
        Dictionary mapping second_level_id to parquet bytes (ready for HTTP submission)
    """

    if isinstance(data_structure, TimeSeriesStructure):
        return serialize_time_series_to_parquet(data_structure)
    elif isinstance(data_structure, TimeSeriesAggregationStructure):
        return serialize_time_series_aggregation_to_parquet(data_structure)
    else:
        raise ValueError(
            f"Expected TimeSeriesStructure or TimeSeriesAggregationStructure, got {type(data_structure).__name__}")


def deserialize_parquet_to_dataframes(
    parquet_data: Dict[str, bytes],
    first_level_id: str,
    only_metadata: bool = False
) -> Union[TimeSeriesStructure, TimeSeriesAggregationStructure, MetadataStructure, TimeSeriesAggregationMetadataStructure]:
    """
    Deserialize parquet data back to a dataclass data structure.

    This is the reverse operation of serialize_dataframes_to_parquet.
    Takes parquet bytes from HTTP submission and converts them back to dataclass instances.

    This is a unified API that delegates to the specific submodule implementations.

    Args:
        parquet_data: Dictionary mapping second_level_id to parquet bytes (from HTTP)
        first_level_id: The first level ID of the data structure
        only_metadata: If True, only return metadata structure without main data

    Returns:
        A TimeSeriesStructure or TimeSeriesAggregationStructure or MetadataStructure or TimeSeriesAggregationMetadataStructure instance
    """

    if first_level_id == "time_series":
        return deserialize_time_series_from_parquet(parquet_data, only_metadata)
    elif first_level_id == "time_series_aggregation":
        return deserialize_time_series_aggregation_from_parquet(parquet_data, only_metadata)
    else:
        raise ValueError(f"Unsupported first level ID: {first_level_id}")
