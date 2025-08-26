import pandas as pd
from typing import Union
from synesis_data_structures.time_series.definitions import (
    TIME_SERIES_DATA_SECOND_LEVEL_ID,
    TIME_SERIES_ENTITY_METADATA_SECOND_LEVEL_ID,
    TIME_SERIES_AGGREGATION_OUTPUTS_SECOND_LEVEL_ID,
    TIME_SERIES_AGGREGATION_INPUTS_SECOND_LEVEL_ID,
    TIME_SERIES_AGGREGATION_METADATA_SECOND_LEVEL_ID,
    FEATURE_INFORMATION_SECOND_LEVEL_ID
)
from synesis_data_structures.time_series.df_dataclasses import (
    TimeSeriesStructure,
    TimeSeriesAggregationStructure
)


def validate_dfs_structure(data_structure: Union[TimeSeriesStructure, TimeSeriesAggregationStructure]) -> None:
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
    metadata_df = data_structure.time_series_entity_metadata
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

    for col in data_df.columns:
        if not _is_snake_case(col):
            errors.append(
                f"Column '{col}' in {TIME_SERIES_DATA_SECOND_LEVEL_ID} should follow snake_case naming convention")

    # Validate entity metadata if present
    if metadata_df is not None and not metadata_df.empty:
        if isinstance(metadata_df.index, pd.MultiIndex):
            errors.append(
                f"{TIME_SERIES_ENTITY_METADATA_SECOND_LEVEL_ID} DataFrame must have single-level index")

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

        for col in metadata_df.columns:
            if not _is_snake_case(col):
                errors.append(
                    f"Column '{col}' in {TIME_SERIES_ENTITY_METADATA_SECOND_LEVEL_ID} should follow snake_case naming convention")

    # Validate feature information if present
    if feature_info_df is not None and not feature_info_df.empty:
        if isinstance(feature_info_df.index, pd.MultiIndex):
            errors.append(
                f"{FEATURE_INFORMATION_SECOND_LEVEL_ID} DataFrame must have single-level index")

        # Check that all data columns have corresponding feature information
        data_columns = set(data_df.columns)
        feature_names = set(feature_info_df.index.astype(str))

        for col in data_columns:
            if col not in feature_names:
                errors.append(
                    f"Feature '{col}' in {TIME_SERIES_DATA_SECOND_LEVEL_ID} not found in feature information")

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

        for col in feature_info_df.columns:
            if not _is_snake_case(col):
                errors.append(
                    f"Column '{col}' in {FEATURE_INFORMATION_SECOND_LEVEL_ID} should follow snake_case naming convention")

    if errors:
        raise ValueError(f"TimeSeries validation failed: {'; '.join(errors)}")


def _validate_time_series_aggregation_dataclass(data_structure: TimeSeriesAggregationStructure) -> None:
    """Validate a TimeSeriesAggregationStructure dataclass instance."""
    errors = []

    outputs_df = data_structure.time_series_aggregation_outputs
    inputs_df = data_structure.time_series_aggregation_inputs
    metadata_df = data_structure.time_series_aggregation_metadata
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

    for col in outputs_df.columns:
        if not _is_snake_case(col):
            errors.append(
                f"Column '{col}' in {TIME_SERIES_AGGREGATION_OUTPUTS_SECOND_LEVEL_ID} should follow snake_case naming convention")

    if len(outputs_df.columns) == 0:
        errors.append(
            f"{TIME_SERIES_AGGREGATION_OUTPUTS_SECOND_LEVEL_ID} DataFrame must have at least one output value column")

    for col in outputs_df.columns:
        if col != 'id':
            col_dtype = outputs_df[col].dtype
            if not pd.api.types.is_numeric_dtype(col_dtype):
                errors.append(
                    f"Output value column '{col}' in {TIME_SERIES_AGGREGATION_OUTPUTS_SECOND_LEVEL_ID} must be numeric, got: {col_dtype}")

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

        for col in inputs_df.columns:
            if not _is_snake_case(col):
                errors.append(
                    f"Column '{col}' in {TIME_SERIES_AGGREGATION_INPUTS_SECOND_LEVEL_ID} should follow snake_case naming convention")

    # Validate aggregation metadata if present
    if metadata_df is not None and not metadata_df.empty:
        if isinstance(metadata_df.index, pd.MultiIndex):
            errors.append(
                f"{TIME_SERIES_AGGREGATION_METADATA_SECOND_LEVEL_ID} DataFrame must have single-level index")

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

        for col in metadata_df.columns:
            if not _is_snake_case(col):
                errors.append(
                    f"Column '{col}' in {TIME_SERIES_AGGREGATION_METADATA_SECOND_LEVEL_ID} should follow snake_case naming convention")

    # Validate feature information if present
    if feature_info_df is not None and not feature_info_df.empty:
        if isinstance(feature_info_df.index, pd.MultiIndex):
            errors.append(
                f"{FEATURE_INFORMATION_SECOND_LEVEL_ID} DataFrame must have single-level index")

        # Check that all output columns have corresponding feature information
        output_columns = set(
            [col for col in outputs_df.columns if col != 'id'])
        feature_names = set(feature_info_df.index.astype(str))

        for col in output_columns:
            if col not in feature_names:
                errors.append(
                    f"Feature '{col}' in {TIME_SERIES_AGGREGATION_OUTPUTS_SECOND_LEVEL_ID} not found in feature information")

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

        for col in feature_info_df.columns:
            if not _is_snake_case(col):
                errors.append(
                    f"Column '{col}' in {FEATURE_INFORMATION_SECOND_LEVEL_ID} should follow snake_case naming convention")

    if errors:
        raise ValueError(
            f"TimeSeriesAggregation validation failed: {'; '.join(errors)}")


def _is_snake_case(text: str) -> bool:
    """Check if a string follows snake_case naming convention."""
    if not text or text.startswith('_') or text.endswith('_'):
        return False

    # Check for consecutive underscores
    if '__' in text:
        return False

    # Check for uppercase letters (should be lowercase in snake_case)
    if any(c.isupper() for c in text):
        return False

    # Check for spaces or other non-alphanumeric characters except underscores
    if any(c not in 'abcdefghijklmnopqrstuvwxyz0123456789_' for c in text.lower()):
        return False

    return True
