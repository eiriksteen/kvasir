import pandas as pd
from typing import Union
from synesis_data_structures.time_series.definitions import (
    TIME_SERIES_DATA_SECOND_LEVEL_ID,
    TIME_SERIES_AGGREGATION_OUTPUTS_SECOND_LEVEL_ID,
    TIME_SERIES_AGGREGATION_INPUTS_SECOND_LEVEL_ID,
    ENTITY_METADATA_SECOND_LEVEL_ID,
    FEATURE_INFORMATION_SECOND_LEVEL_ID
)
from synesis_data_structures.time_series.df_dataclasses import (
    TimeSeriesStructure,
    TimeSeriesAggregationStructure
)


def validate_object_group_structure(data_structure: Union[TimeSeriesStructure, TimeSeriesAggregationStructure]) -> None:
    """
    Validate a dataclass data structure.

    Args:
        data_structure: A TimeSeriesStructure or TimeSeriesAggregationStructure instance
    """
    if isinstance(data_structure, TimeSeriesStructure):
        _validate_time_series_dataclass(data_structure)
    elif isinstance(data_structure, TimeSeriesAggregationStructure):
        _validate_time_series_aggregation_dataclass(data_structure)
    else:
        raise ValueError(
            f"Expected TimeSeriesStructure or TimeSeriesAggregationStructure, got {type(data_structure).__name__}")


def _validate_time_series_dataclass(data_structure: TimeSeriesStructure) -> None:
    """Validate a TimeSeriesStructure dataclass instance."""
    errors = []

    data_df = data_structure.time_series_data
    metadata_df = data_structure.entity_metadata
    feature_info_df = data_structure.feature_information

    if data_df is None:
        errors.append(
            f"{TIME_SERIES_DATA_SECOND_LEVEL_ID} DataFrame is required")
        raise ValueError(f"TimeSeries validation failed: {'; '.join(errors)}")

    if data_df.empty:
        errors.append(
            f"{TIME_SERIES_DATA_SECOND_LEVEL_ID} DataFrame cannot be empty")

    if not isinstance(data_df.index, pd.MultiIndex):
        errors.append(
            f"{TIME_SERIES_DATA_SECOND_LEVEL_ID} DataFrame must have MultiIndex with 2 levels (entity_id, timestamp)")

    if isinstance(data_df.index, pd.MultiIndex) and len(data_df.index.levels) != 2:
        errors.append(
            f"{TIME_SERIES_DATA_SECOND_LEVEL_ID} DataFrame must have exactly 2 index levels, got {len(data_df.index.levels)}")

    if isinstance(data_df.index, pd.MultiIndex):
        level_1_values = data_df.index.get_level_values(1)
        if not pd.api.types.is_datetime64_any_dtype(level_1_values):
            errors.append(
                "Level 1 of MultiIndex must contain datetime objects")

    # Validate that all data columns are numeric (int or float)
    for col in data_df.columns:
        col_dtype = data_df[col].dtype
        if not pd.api.types.is_numeric_dtype(col_dtype):
            errors.append(
                f"Column '{col}' in {TIME_SERIES_DATA_SECOND_LEVEL_ID} must be numeric (int or float), got: {col_dtype}. "
                f"Categorical features should be stored as 0-indexed integers with string labels defined in {FEATURE_INFORMATION_SECOND_LEVEL_ID}.")

    # Validate entity metadata

    if isinstance(metadata_df.index, pd.MultiIndex):
        errors.append(
            f"{ENTITY_METADATA_SECOND_LEVEL_ID} DataFrame must have single-level index")

    data_entity_ids = set(data_df.index.get_level_values(0).unique())
    metadata_entity_ids = set(metadata_df.index.astype(str))

    for entity_id in data_entity_ids:
        if entity_id not in metadata_entity_ids:
            errors.append(
                f"Entity ID '{entity_id}' in main data not found in metadata")

    for entity_id in metadata_entity_ids:
        if entity_id not in data_entity_ids:
            errors.append(
                f"Entity ID '{entity_id}' in metadata not found in main data")

    # Validate required metadata columns
    required_metadata_columns = ['num_timestamps', 'start_timestamp',
                                 'end_timestamp', 'sampling_frequency', 'timezone']
    missing_metadata_columns = [
        col for col in required_metadata_columns if col not in metadata_df.columns]
    if missing_metadata_columns:
        errors.append(
            f"Missing required columns in {ENTITY_METADATA_SECOND_LEVEL_ID}: {missing_metadata_columns}")

    # Validate sampling_frequency values
    if 'sampling_frequency' in metadata_df.columns:
        valid_frequencies = ['m', 'h', 'd', 'w', 'y', 'irr']
        invalid_frequencies = metadata_df[~metadata_df['sampling_frequency'].isin(
            valid_frequencies)]['sampling_frequency'].unique()
        if len(invalid_frequencies) > 0:
            errors.append(
                f"Invalid sampling_frequency values in {ENTITY_METADATA_SECOND_LEVEL_ID}: {invalid_frequencies}. Must be one of {valid_frequencies}")

    # Validate timestamp columns are datetime
    for col in ['start_timestamp', 'end_timestamp']:
        if col in metadata_df.columns:
            if not pd.api.types.is_datetime64_any_dtype(metadata_df[col]):
                errors.append(
                    f"Column '{col}' in {ENTITY_METADATA_SECOND_LEVEL_ID} must contain datetime objects")

    # Validate num_timestamps is numeric
    if 'num_timestamps' in metadata_df.columns:
        if not pd.api.types.is_integer_dtype(metadata_df['num_timestamps']):
            errors.append(
                f"Column 'num_timestamps' in {ENTITY_METADATA_SECOND_LEVEL_ID} must be integer type")

    # Validate feature information if present
    data_columns = set(data_df.columns)
    _validate_feature_information(
        feature_info_df, data_columns, TIME_SERIES_DATA_SECOND_LEVEL_ID, errors)

    if errors:
        raise ValueError(f"TimeSeries validation failed: {'; '.join(errors)}")


def _validate_time_series_aggregation_dataclass(data_structure: TimeSeriesAggregationStructure) -> None:
    """Validate a TimeSeriesAggregationStructure dataclass instance."""
    errors = []

    outputs_df = data_structure.time_series_aggregation_outputs
    inputs_df = data_structure.time_series_aggregation_inputs
    metadata_df = data_structure.entity_metadata
    feature_info_df = data_structure.feature_information

    if outputs_df is None:
        errors.append(
            f"{TIME_SERIES_AGGREGATION_OUTPUTS_SECOND_LEVEL_ID} DataFrame is required")
        raise ValueError(
            f"TimeSeriesAggregation validation failed: {'; '.join(errors)}")

    if outputs_df.empty:
        errors.append(
            f"{TIME_SERIES_AGGREGATION_OUTPUTS_SECOND_LEVEL_ID} DataFrame cannot be empty")

    if not isinstance(outputs_df.index, pd.RangeIndex):
        errors.append(
            f"{TIME_SERIES_AGGREGATION_OUTPUTS_SECOND_LEVEL_ID} DataFrame must have simple integer index")

    if len(outputs_df.columns) == 0:
        errors.append(
            f"{TIME_SERIES_AGGREGATION_OUTPUTS_SECOND_LEVEL_ID} DataFrame must have at least one output value column")

    # Validate that all output columns (except 'id') are numeric (int or float)
    for col in outputs_df.columns:
        if col != 'id':
            col_dtype = outputs_df[col].dtype
            if not pd.api.types.is_numeric_dtype(col_dtype):
                errors.append(
                    f"Output value column '{col}' in {TIME_SERIES_AGGREGATION_OUTPUTS_SECOND_LEVEL_ID} must be numeric (int or float), got: {col_dtype}. "
                    f"Categorical features should be stored as 0-indexed integers with string labels defined in {FEATURE_INFORMATION_SECOND_LEVEL_ID}.")

    # Validate inputs DataFrame if present
    if inputs_df is not None and not inputs_df.empty:
        required_columns = ['id', 'time_series_id',
                            'input_feature_name', 'start_timestamp', 'end_timestamp']
        missing_columns = [
            col for col in required_columns if col not in inputs_df.columns]
        if missing_columns:
            errors.append(
                f"Missing required columns in {TIME_SERIES_AGGREGATION_INPUTS_SECOND_LEVEL_ID}: {missing_columns}")

        if 'id' in inputs_df.columns and 'id' in outputs_df.columns:
            input_agg_ids = set(inputs_df['id'].astype(str))
            output_agg_ids = set(outputs_df['id'].astype(str))

            missing_ids = input_agg_ids - output_agg_ids
            if missing_ids:
                errors.append(
                    f"Missing aggregation IDs in outputs: {missing_ids}")

        for col in ['start_timestamp', 'end_timestamp']:
            if col in inputs_df.columns:
                if not pd.api.types.is_datetime64_any_dtype(inputs_df[col]):
                    errors.append(
                        f"Column '{col}' in {TIME_SERIES_AGGREGATION_INPUTS_SECOND_LEVEL_ID} must contain datetime objects")

    # Validate aggregation metadata
    if isinstance(metadata_df.index, pd.MultiIndex):
        errors.append(
            f"{ENTITY_METADATA_SECOND_LEVEL_ID} DataFrame must have single-level index")

    # Check that all aggregation IDs in outputs have corresponding metadata
    if 'id' in outputs_df.columns:
        output_agg_ids = set(outputs_df['id'].astype(str))
        metadata_agg_ids = set(metadata_df.index.astype(str))

        for agg_id in output_agg_ids:
            if agg_id not in metadata_agg_ids:
                errors.append(
                    f"Aggregation ID '{agg_id}' in outputs not found in metadata")

        for agg_id in metadata_agg_ids:
            if agg_id not in output_agg_ids:
                errors.append(
                    f"Aggregation ID '{agg_id}' in metadata not found in outputs")

        # Validate required metadata columns
        required_metadata_columns = ['is_multi_series_computation']
        missing_metadata_columns = [
            col for col in required_metadata_columns if col not in metadata_df.columns]
        if missing_metadata_columns:
            errors.append(
                f"Missing required columns in {ENTITY_METADATA_SECOND_LEVEL_ID}: {missing_metadata_columns}")

        # Validate is_multi_series_computation is boolean
        if 'is_multi_series_computation' in metadata_df.columns:
            if not pd.api.types.is_bool_dtype(metadata_df['is_multi_series_computation']):
                errors.append(
                    f"Column 'is_multi_series_computation' in {ENTITY_METADATA_SECOND_LEVEL_ID} must be boolean type")

    # Validate feature information if present
    output_columns = set(
        [col for col in outputs_df.columns if col != 'id'])
    _validate_feature_information(
        feature_info_df, output_columns, TIME_SERIES_AGGREGATION_OUTPUTS_SECOND_LEVEL_ID, errors)

    if errors:
        raise ValueError(
            f"TimeSeriesAggregation validation failed: {'; '.join(errors)}")


def _validate_feature_information(
    feature_info_df: pd.DataFrame,
    expected_features: set,
    source_df_name: str,
    errors: list
) -> None:
    """
    Validate feature information DataFrame structure and contents.

    Args:
        feature_info_df: The feature information DataFrame to validate
        expected_features: Set of feature names that should be present
        source_df_name: Name of source DataFrame for error messages
        errors: List to append error messages to
    """
    if isinstance(feature_info_df.index, pd.MultiIndex):
        errors.append(
            f"{FEATURE_INFORMATION_SECOND_LEVEL_ID} DataFrame must have single-level index")

    # Validate index name
    if feature_info_df.index.name != 'name':
        errors.append(
            f"{FEATURE_INFORMATION_SECOND_LEVEL_ID} DataFrame index must be named 'name', got: {feature_info_df.index.name}")

    # Validate index dtype is string
    if not pd.api.types.is_string_dtype(feature_info_df.index):
        errors.append(
            f"{FEATURE_INFORMATION_SECOND_LEVEL_ID} DataFrame index must be string type, got: {feature_info_df.index.dtype}")

    # Check that all expected features have corresponding feature information
    feature_names = set(feature_info_df.index.astype(str))

    for col in expected_features:
        if col not in feature_names:
            errors.append(
                f"Feature '{col}' in {source_df_name} not found in feature information")

    # Validate required columns in feature information
    required_columns = ['unit', 'description',
                        'type', 'subtype', 'scale', 'source']
    missing_columns = [
        col for col in required_columns if col not in feature_info_df.columns]
    if missing_columns:
        errors.append(
            f"Missing required columns in {FEATURE_INFORMATION_SECOND_LEVEL_ID}: {missing_columns}")

    # Validate type values
    if 'type' in feature_info_df.columns:
        valid_types = ['numerical', 'categorical']
        invalid_types = feature_info_df[~feature_info_df['type'].isin(
            valid_types)]['type'].unique()
        if len(invalid_types) > 0:
            errors.append(
                f"Invalid type values in {FEATURE_INFORMATION_SECOND_LEVEL_ID}: {invalid_types}")

    # Validate subtype values
    if 'subtype' in feature_info_df.columns:
        valid_subtypes = ['continuous', 'discrete']
        invalid_subtypes = feature_info_df[~feature_info_df['subtype'].isin(
            valid_subtypes)]['subtype'].unique()
        if len(invalid_subtypes) > 0:
            errors.append(
                f"Invalid subtype values in {FEATURE_INFORMATION_SECOND_LEVEL_ID}: {invalid_subtypes}")

    # Validate scale values
    if 'scale' in feature_info_df.columns:
        valid_scales = ['ratio', 'interval', 'ordinal', 'nominal']
        invalid_scales = feature_info_df[~feature_info_df['scale'].isin(
            valid_scales)]['scale'].unique()
        if len(invalid_scales) > 0:
            errors.append(
                f"Invalid scale values in {FEATURE_INFORMATION_SECOND_LEVEL_ID}: {invalid_scales}")

    # Validate source values
    if 'source' in feature_info_df.columns:
        valid_sources = ['data', 'metadata']
        invalid_sources = feature_info_df[~feature_info_df['source'].isin(
            valid_sources)]['source'].unique()
        if len(invalid_sources) > 0:
            errors.append(
                f"Invalid source values in {FEATURE_INFORMATION_SECOND_LEVEL_ID}: {invalid_sources}")
