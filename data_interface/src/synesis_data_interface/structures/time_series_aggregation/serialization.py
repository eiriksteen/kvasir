import pandas as pd
import numpy as np
import uuid
import io
from datetime import datetime, timedelta
from typing import List, Dict

from synesis_data_interface.structures.time_series_aggregation.schema import TimeSeriesAggregation
from synesis_data_interface.structures.time_series_aggregation.definitions import (
    TIME_SERIES_AGGREGATION_OUTPUTS_SECOND_LEVEL_ID,
    TIME_SERIES_AGGREGATION_INPUTS_SECOND_LEVEL_ID,
    ENTITY_METADATA_SECOND_LEVEL_ID,
    FEATURE_INFORMATION_SECOND_LEVEL_ID
)
from synesis_data_interface.structures.time_series_aggregation.raw import (
    TimeSeriesAggregationStructure,
    TimeSeriesAggregationMetadataStructure
)
from synesis_data_interface.structures.utils import simplify_dtype
from synesis_data_interface.structures.overview import get_second_level_ids_for_structure


# Functions to:
#     - Send data objects through API to client
#     - Send / receive parquet of data objects through API to processing unit

# Public API


def serialize_time_series_aggregation_structure_to_api_payloads(data_structure: TimeSeriesAggregationStructure) -> List[TimeSeriesAggregation]:
    """
    Serialize a dataclass data structure to API payload objects for sending to client.

    Args:
        data_structure: A TimeSeriesStructure or TimeSeriesAggregationStructure instance

    Returns:
        List of API payload objects (TimeSeries or TimeSeriesAggregation)
    """

    """Convert TimeSeriesAggregationStructure to TimeSeriesAggregation API payloads."""
    outputs_df = data_structure.time_series_aggregation_outputs
    inputs_df = data_structure.time_series_aggregation_inputs
    metadata_df = data_structure.entity_metadata
    feature_info_df = data_structure.feature_information

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
                ENTITY_METADATA_SECOND_LEVEL_ID: agg_metadata.to_dict()
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
            structure_type="time_series_aggregation",
            additional_variables=additional_variables,
            features=feature_information
        )
        payloads.append(payload)

    return payloads


def serialize_dataframes_to_parquet(data_structure: TimeSeriesAggregationStructure) -> Dict[str, bytes]:
    """
    Serialize a dataclass data structure to parquet format for processing unit.

    This function takes the DataFrames and returns them as bytes ready for direct HTTP submission.
    The output is a dictionary with second_level_id as key and the corresponding parquet bytes as value.

    Args:
        data_structure: A TimeSeriesStructure or TimeSeriesAggregationStructure instance

    Returns:
        Dictionary mapping second_level_id to parquet bytes (ready for HTTP submission)
    """

    first_level_id = "time_series_aggregation"
    dataframes = {
        TIME_SERIES_AGGREGATION_OUTPUTS_SECOND_LEVEL_ID: data_structure.time_series_aggregation_outputs,
        TIME_SERIES_AGGREGATION_INPUTS_SECOND_LEVEL_ID: data_structure.time_series_aggregation_inputs,
        ENTITY_METADATA_SECOND_LEVEL_ID: data_structure.entity_metadata,
        FEATURE_INFORMATION_SECOND_LEVEL_ID: data_structure.feature_information
    }

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
        if df is not None and not df.empty:
            # Use in-memory buffer to serialize DataFrame to parquet bytes
            buffer = io.BytesIO()
            df.to_parquet(buffer, index=True)
            parquet_bytes[second_level_id] = buffer.getvalue()
        else:
            # For None or empty DataFrames, create an empty parquet file
            buffer = io.BytesIO()
            empty_df = pd.DataFrame()
            empty_df.to_parquet(buffer, index=True)
            parquet_bytes[second_level_id] = buffer.getvalue()

    return parquet_bytes


def deserialize_parquet_to_dataframes(
    parquet_data: Dict[str, bytes],
    only_metadata: bool = False
) -> TimeSeriesAggregationStructure | TimeSeriesAggregationMetadataStructure:
    """
    Deserialize parquet data back to a TimeSeriesAggregationStructure.

    This is the reverse operation of serialize_dataframes_to_parquet.
    Takes parquet bytes from HTTP submission and converts them back to a TimeSeriesAggregationStructure.

    Args:
        parquet_data: Dictionary mapping second_level_id to parquet bytes (from HTTP)
        only_metadata: If True, only return TimeSeriesAggregationMetadataStructure without aggregation outputs

    Returns:
        A TimeSeriesAggregationStructure or TimeSeriesAggregationMetadataStructure instance
    """

    first_level_id = "time_series_aggregation"

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

    # Convert to appropriate dataclass
    metadata = TimeSeriesAggregationMetadataStructure(
        entity_metadata=dataframes.get(ENTITY_METADATA_SECOND_LEVEL_ID),
        feature_information=dataframes.get(
            FEATURE_INFORMATION_SECOND_LEVEL_ID),
        time_series_aggregation_inputs=dataframes.get(
            TIME_SERIES_AGGREGATION_INPUTS_SECOND_LEVEL_ID)
    )
    if only_metadata:
        return metadata
    else:
        assert TIME_SERIES_AGGREGATION_OUTPUTS_SECOND_LEVEL_ID in dataframes and TIME_SERIES_AGGREGATION_INPUTS_SECOND_LEVEL_ID in dataframes, "No aggregation data provided, can only return metadata"
        return TimeSeriesAggregationStructure(
            time_series_aggregation_outputs=dataframes.get(
                TIME_SERIES_AGGREGATION_OUTPUTS_SECOND_LEVEL_ID),
            entity_metadata=metadata.entity_metadata,
            feature_information=metadata.feature_information,
            time_series_aggregation_inputs=metadata.time_series_aggregation_inputs
        )
