import pandas as pd
import uuid
import io
from datetime import datetime
from typing import List, Union, Dict
from synesis_data_structures.time_series.schema import (
    TimeSeries,
    TimeSeriesAggregation
)
from synesis_data_structures.time_series.definitions import get_second_level_ids_for_structure


# Functions to:
#     - Send data objects through API to client
#     - Send / receive parquet of data objects through API to processing unit

# Public API

def serialize_dataframes_to_api_payloads(dataframes: Dict[str, pd.DataFrame], first_level_id: str) -> List[Union[TimeSeries, TimeSeriesAggregation]]:
    """
    Serialize a first level data structure to API payload objects for sending to client.

    Args:
        dataframes: Dictionary mapping second_level_id to DataFrame
        first_level_id: The first level ID of the data structure

    Returns:
        List of API payload objects (TimeSeries or TimeSeriesAggregation)
    """
    # Map first level IDs to their corresponding private serialization functions
    serialization_mapping = {
        "time_series": _serialize_time_series_dfs_to_api_payload,
        "time_series_aggregation": _serialize_time_series_aggregation_dfs_to_api_payload
    }

    if first_level_id not in serialization_mapping:
        raise ValueError(f"Unknown first level ID: {first_level_id}")

    # Use the appropriate private serialization function
    return serialization_mapping[first_level_id](dataframes)


def serialize_dataframes_to_parquet(dataframes: Dict[str, pd.DataFrame], first_level_id: str) -> Dict[str, bytes]:
    """
    Serialize a first level data structure to parquet format for processing unit.

    This function takes the DataFrames and returns them as bytes ready for direct HTTP submission.
    The output is a dictionary with second_level_id as key and the corresponding parquet bytes as value.

    Args:
        dataframes: Dictionary mapping second_level_id to DataFrame
        first_level_id: The first level ID of the data structure

    Returns:
        Dictionary mapping second_level_id to parquet bytes (ready for HTTP submission)
    """

    # Get the expected second level IDs for this structure
    expected_second_level_ids = get_second_level_ids_for_structure(
        first_level_id)

    # Validate that all expected second level IDs are present
    missing_ids = set(expected_second_level_ids) - set(dataframes.keys())
    if missing_ids:
        raise ValueError(f"Missing required second level IDs: {missing_ids}")

    # Serialize each DataFrame to parquet bytes using in-memory buffer
    parquet_bytes = {}
    for second_level_id, df in dataframes.items():
        if not df.empty:
            # Use in-memory buffer to serialize DataFrame to parquet bytes
            buffer = io.BytesIO()
            df.to_parquet(buffer, index=True)
            parquet_bytes[second_level_id] = buffer.getvalue()
        else:
            # For empty DataFrames, create an empty parquet file
            buffer = io.BytesIO()
            df.to_parquet(buffer, index=True)
            parquet_bytes[second_level_id] = buffer.getvalue()

    return parquet_bytes


def deserialize_parquet_to_dataframes(parquet_data: Dict[str, bytes], first_level_id: str) -> Dict[str, pd.DataFrame]:
    """
    Deserialize parquet data back to a first level data structure.

    This is the reverse operation of serialize_dataframes_to_parquet.
    Takes parquet bytes from HTTP submission and converts them back to DataFrames.

    Args:
        parquet_data: Dictionary mapping second_level_id to parquet bytes (from HTTP)
        first_level_id: The first level ID of the data structure

    Returns:
        Dictionary mapping second_level_id to DataFrame in the expected format
    """

    # Get the expected second level IDs for this structure
    expected_second_level_ids = get_second_level_ids_for_structure(
        first_level_id)

    parquet_keys_are_subset_of_expected_second_level_ids = set(
        parquet_data.keys()) <= set(expected_second_level_ids)

    if not parquet_keys_are_subset_of_expected_second_level_ids:
        raise ValueError(
            f"Second level IDs in parquet data are not a subset of expected second level IDs, expected: {expected_second_level_ids}, got: {parquet_data.keys()}")

    # Deserialize each parquet bytes to DataFrame using in-memory buffer
    dataframes = {}
    for second_level_id, parquet_bytes in parquet_data.items():
        # Use in-memory buffer to deserialize parquet bytes to DataFrame
        buffer = io.BytesIO(parquet_bytes)
        df = pd.read_parquet(buffer)
        dataframes[second_level_id] = df

    return dataframes


# Private API

def _serialize_time_series_dfs_to_api_payload(dataframes: Dict[str, pd.DataFrame]) -> List[TimeSeries]:
    """Convert TimeSeries DataFrames to TimeSeries API payloads."""
    data_df = dataframes.get("time_series_data")
    metadata_df = dataframes.get("time_series_entity_metadata")
    feature_info_df = dataframes.get("time_series_feature_information")

    if data_df is None:
        raise ValueError("time_series_data DataFrame is required")

    if not isinstance(data_df.index, pd.MultiIndex) or len(data_df.index.levels) != 2:
        raise ValueError(
            "TimeSeries DataFrame must have MultiIndex with 2 levels (entity_id, timestamp)")

    entity_ids = data_df.index.get_level_values(0).unique()
    payloads = []

    for entity_id in entity_ids:
        entity_data = data_df.loc[entity_id]

        # Convert DataFrame to dict of feature_name -> list of (timestamp, value)
        data = {}
        for column in entity_data.columns:
            # Filter out NaN values and convert to list of tuples
            valid_data = entity_data[column].dropna()
            data[column] = list(zip(valid_data.index, valid_data.values))

        # Generate UUID for the time series
        time_series_id = uuid.uuid4()

        # Prepare additional_variables with metadata if available
        additional_variables = None
        if metadata_df is not None and not metadata_df.empty and entity_id in metadata_df.index:
            entity_metadata = metadata_df.loc[entity_id]
            additional_variables = {
                "entity_metadata": entity_metadata.to_dict()
            }

        # Prepare feature_information if available
        feature_information = {}
        if feature_info_df is not None and not feature_info_df.empty:
            for feature_name in data.keys():
                if feature_name in feature_info_df.index:
                    feature_row = feature_info_df.loc[feature_name]
                    feature_information[feature_name] = {
                        "name": feature_name,
                        "unit": feature_row.get("unit", ""),
                        "description": feature_row.get("description", ""),
                        "type": feature_row.get("type", "numerical"),
                        "subtype": feature_row.get("subtype", "continuous"),
                        "scale": feature_row.get("scale", "ratio"),
                        "source": feature_row.get("source", "data"),
                        "category_id": feature_row.get("category_id")
                    }

        payload = TimeSeries(
            id=time_series_id,
            data=data,
            name=f"TimeSeries_{entity_id}",
            description=f"Time series data for entity {entity_id}",
            structure_type="time_series",
            additional_variables=additional_variables,
            features=feature_information,
            created_at=datetime.now(),
            updated_at=datetime.now()
        )
        payloads.append(payload)

    return payloads


def _serialize_time_series_aggregation_dfs_to_api_payload(dataframes: Dict[str, pd.DataFrame]) -> List[TimeSeriesAggregation]:
    """Convert TimeSeriesAggregation DataFrames to TimeSeriesAggregation API payloads."""
    outputs_df = dataframes.get("time_series_aggregation_outputs")
    inputs_df = dataframes.get("time_series_aggregation_inputs")
    metadata_df = dataframes.get("time_series_aggregation_metadata")
    feature_info_df = dataframes.get("time_series_feature_information")

    if outputs_df is None:
        raise ValueError(
            "time_series_aggregation_outputs DataFrame is required")

    payloads = []

    # Group by aggregation ID
    if 'id' in outputs_df.columns:
        agg_ids = outputs_df['id'].unique()
    else:
        # If no id column, treat the entire DataFrame as one aggregation
        agg_ids = [uuid.uuid4()]

    for agg_id in agg_ids:
        if 'id' in outputs_df.columns:
            agg_outputs = outputs_df[outputs_df['id'] == agg_id]
        else:
            agg_outputs = outputs_df

        # Convert DataFrame to output_data dict
        output_data = {}
        for column in agg_outputs.columns:
            if column != 'id':
                # Convert column values to list, filtering out NaN
                values = agg_outputs[column].dropna().tolist()
                output_data[column] = values

        # Convert inputs DataFrame to input_data dict
        input_data = {}
        if inputs_df is not None and not inputs_df.empty:
            if 'id' in inputs_df.columns:
                agg_inputs = inputs_df[inputs_df['id'] == agg_id]
            else:
                agg_inputs = inputs_df

            for _, row in agg_inputs.iterrows():
                time_series_id = row.get('time_series_id', uuid.uuid4())
                input_feature_name = row.get('input_feature_name', 'unknown')
                start_timestamp = row.get('start_timestamp')
                end_timestamp = row.get('end_timestamp')

                if start_timestamp is not None and end_timestamp is not None:
                    input_data[(time_series_id, input_feature_name)] = (
                        start_timestamp, end_timestamp)

        # Generate UUID for the aggregation
        aggregation_id = uuid.uuid4()

        # Prepare additional_variables with metadata if available
        additional_variables = None
        if metadata_df is not None and not metadata_df.empty and str(agg_id) in metadata_df.index:
            agg_metadata = metadata_df.loc[str(agg_id)]
            additional_variables = {
                "aggregation_metadata": agg_metadata.to_dict()
            }

        # Prepare feature_information for outputs if available
        feature_information = {}
        if feature_info_df is not None and not feature_info_df.empty:
            for feature_name in output_data.keys():
                if feature_name in feature_info_df.index:
                    feature_row = feature_info_df.loc[feature_name]
                    feature_information[feature_name] = {
                        "name": feature_name,
                        "unit": feature_row.get("unit", ""),
                        "description": feature_row.get("description", ""),
                        "type": feature_row.get("type", "numerical"),
                        "subtype": feature_row.get("subtype", "continuous"),
                        "scale": feature_row.get("scale", "ratio"),
                        "source": feature_row.get("source", "data"),
                        "category_id": feature_row.get("category_id")
                    }

        payload = TimeSeriesAggregation(
            id=aggregation_id,
            input_data=input_data,
            output_data=output_data,
            name=f"TimeSeriesAggregation_{aggregation_id}",
            description=f"Time series aggregation {aggregation_id}",
            structure_type="time_series_aggregation",
            additional_variables=additional_variables,
            features=feature_information,
            created_at=datetime.now(),
            updated_at=datetime.now()
        )
        payloads.append(payload)

    return payloads
