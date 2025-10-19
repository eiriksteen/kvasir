import pandas as pd
import numpy as np
import uuid
import io
from datetime import datetime, timedelta
from typing import List, Union, Dict
from synesis_data_structures.time_series.schema import (
    TimeSeries,
    TimeSeriesAggregation
)
from synesis_data_structures.time_series.definitions import (
    FEATURE_INFORMATION_SECOND_LEVEL_ID,
    ENTITY_METADATA_SECOND_LEVEL_ID,
    TIME_SERIES_DATA_SECOND_LEVEL_ID,
    TIME_SERIES_AGGREGATION_OUTPUTS_SECOND_LEVEL_ID,
    TIME_SERIES_AGGREGATION_INPUTS_SECOND_LEVEL_ID,
    get_second_level_ids_for_structure
)
from synesis_data_structures.time_series.df_dataclasses import (
    TimeSeriesStructure,
    TimeSeriesAggregationStructure,
    MetadataStructure,
    TimeSeriesAggregationMetadataStructure
)
from synesis_data_structures.base_schema import RawDataStructure, AggregationOutput, Column
from synesis_data_structures.utils import simplify_dtype


# Functions to:
#     - Send data objects through API to client
#     - Send / receive parquet of data objects through API to processing unit

# Public API

def serialize_dataframes_to_api_payloads(data_structure: Union[TimeSeriesStructure, TimeSeriesAggregationStructure]) -> List[Union[TimeSeries, TimeSeriesAggregation]]:
    """
    Serialize a dataclass data structure to API payload objects for sending to client.

    Args:
        data_structure: A TimeSeriesStructure or TimeSeriesAggregationStructure instance

    Returns:
        List of API payload objects (TimeSeries or TimeSeriesAggregation)
    """

    if isinstance(data_structure, TimeSeriesStructure):
        return _serialize_time_series_dataclass_to_api_payload(data_structure)
    elif isinstance(data_structure, TimeSeriesAggregationStructure):
        return _serialize_time_series_aggregation_dataclass_to_api_payload(data_structure)
    else:
        raise ValueError(
            f"Expected TimeSeriesStructure or TimeSeriesAggregationStructure, got {type(data_structure).__name__}")


def serialize_dataframes_to_parquet(data_structure: Union[TimeSeriesStructure, TimeSeriesAggregationStructure]) -> Dict[str, bytes]:
    """
    Serialize a dataclass data structure to parquet format for processing unit.

    This function takes the DataFrames and returns them as bytes ready for direct HTTP submission.
    The output is a dictionary with second_level_id as key and the corresponding parquet bytes as value.

    Args:
        data_structure: A TimeSeriesStructure or TimeSeriesAggregationStructure instance

    Returns:
        Dictionary mapping second_level_id to parquet bytes (ready for HTTP submission)
    """

    if isinstance(data_structure, TimeSeriesStructure):
        first_level_id = "time_series"
        dataframes = {
            TIME_SERIES_DATA_SECOND_LEVEL_ID: data_structure.time_series_data,
            ENTITY_METADATA_SECOND_LEVEL_ID: data_structure.entity_metadata,
            FEATURE_INFORMATION_SECOND_LEVEL_ID: data_structure.feature_information
        }
    elif isinstance(data_structure, TimeSeriesAggregationStructure):
        first_level_id = "time_series_aggregation"
        dataframes = {
            TIME_SERIES_AGGREGATION_OUTPUTS_SECOND_LEVEL_ID: data_structure.time_series_aggregation_outputs,
            TIME_SERIES_AGGREGATION_INPUTS_SECOND_LEVEL_ID: data_structure.time_series_aggregation_inputs,
            ENTITY_METADATA_SECOND_LEVEL_ID: data_structure.entity_metadata,
            FEATURE_INFORMATION_SECOND_LEVEL_ID: data_structure.feature_information
        }
    else:
        raise ValueError(
            f"Expected TimeSeriesStructure or TimeSeriesAggregationStructure, got {type(data_structure).__name__}")

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
    first_level_id: str,
    only_metadata: bool = False
) -> Union[TimeSeriesStructure, TimeSeriesAggregationStructure, MetadataStructure, TimeSeriesAggregationMetadataStructure]:
    """
    Deserialize parquet data back to a dataclass data structure.

    This is the reverse operation of serialize_dataframes_to_parquet.
    Takes parquet bytes from HTTP submission and converts them back to dataclass instances.

    Args:
        parquet_data: Dictionary mapping second_level_id to parquet bytes (from HTTP)
        first_level_id: The first level ID of the data structure

    Returns:
        A TimeSeriesStructure or TimeSeriesAggregationStructure or MetadataStructure or TimeSeriesAggregationMetadataStructure instance
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

    # Convert to appropriate dataclass
    if first_level_id == "time_series":
        metadata = MetadataStructure(
            entity_metadata=dataframes.get(ENTITY_METADATA_SECOND_LEVEL_ID),
            feature_information=dataframes.get(
                FEATURE_INFORMATION_SECOND_LEVEL_ID)
        )
        if only_metadata:
            return metadata
        else:
            assert TIME_SERIES_DATA_SECOND_LEVEL_ID in dataframes, "No time series data provided, can only return metadata"
            return TimeSeriesStructure(
                time_series_data=dataframes.get(
                    TIME_SERIES_DATA_SECOND_LEVEL_ID),
                **metadata
            )

    elif first_level_id == "time_series_aggregation":
        metadata = MetadataStructure(
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
                **metadata
            )
    else:
        raise ValueError(f"Unsupported first level ID: {first_level_id}")


# Private API

def _serialize_time_series_dataclass_to_api_payload(data_structure: TimeSeriesStructure) -> List[TimeSeries]:
    """Convert TimeSeriesStructure to TimeSeries API payloads."""
    data_df = data_structure.time_series_data
    metadata_df = data_structure.entity_metadata
    feature_info_df = data_structure.feature_information

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
                ENTITY_METADATA_SECOND_LEVEL_ID: entity_metadata.to_dict()
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
            structure_type="time_series",
            additional_variables=additional_variables,
            features=feature_information,
        )
        payloads.append(payload)

    return payloads


def _serialize_time_series_aggregation_dataclass_to_api_payload(data_structure: TimeSeriesAggregationStructure) -> List[TimeSeriesAggregation]:
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



def serialize_dataframe_for_aggregation_object(data: pd.DataFrame) -> RawDataStructure:
    columns = []
    new_index_names = []

    counter = 0
    for idx in data.index.names:
        if idx is None:
            new_index_names.append(f'index_{counter}')
            counter += 1
        else:
            new_index_names.append(idx)
    
    data.index.names = new_index_names
    data = data.reset_index()

    # Convert any NaN values to None before serializing
    data = pd.DataFrame(
        data=np.where(pd.isna(data), None, data),
        columns=data.columns,
        index=data.index
    )

    for col_name in data.columns:
        col = data[col_name]
        dtype = simplify_dtype(col.dtype)
        
        columns.append(Column(name=col_name, value_type=dtype, values=col.values.tolist()))

    return RawDataStructure(data=columns)


def serialize_raw_data_for_aggregation_object_for_api(output_data: float | int | str | bool | datetime | timedelta | pd.DataFrame | pd.Series) -> AggregationOutput:
    if isinstance(output_data, float | int | str | bool | datetime | timedelta):
        rwd = AggregationOutput(
            output_data=RawDataStructure({('output_data', type(output_data).__name__): [output_data]}),
        )
        return rwd
    elif isinstance(output_data, pd.DataFrame):
        transformed_output_data = serialize_dataframe_for_aggregation_object(output_data)
        return AggregationOutput(
            output_data=transformed_output_data,
        )

    elif isinstance(output_data, pd.Series):
        output_data = output_data.to_frame(name=output_data.name if output_data.name is not None else 'series')
        transformed_output_data = serialize_dataframe_for_aggregation_object(output_data)
        return AggregationOutput(
            output_data=transformed_output_data,
        )


