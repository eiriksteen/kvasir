import pandas as pd

from synesis_data_interface.structures.time_series_aggregation.definitions import (
    TIME_SERIES_AGGREGATION_OUTPUTS_SECOND_LEVEL_ID,
    TIME_SERIES_AGGREGATION_INPUTS_SECOND_LEVEL_ID,
    ENTITY_METADATA_SECOND_LEVEL_ID,
    FEATURE_INFORMATION_SECOND_LEVEL_ID
)
from synesis_data_interface.structures.time_series_aggregation.raw import TimeSeriesAggregationStructure
from synesis_data_interface.structures.base.validation import validate_feature_information


def validate_time_series_aggregation_dataclass(data_structure: TimeSeriesAggregationStructure) -> None:
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
    validate_feature_information(
        feature_info_df, output_columns, TIME_SERIES_AGGREGATION_OUTPUTS_SECOND_LEVEL_ID, errors)

    if errors:
        raise ValueError(
            f"TimeSeriesAggregation validation failed: {'; '.join(errors)}")
