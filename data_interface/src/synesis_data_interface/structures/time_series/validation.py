import pandas as pd
from synesis_data_interface.structures.time_series.definitions import (
    TIME_SERIES_DATA_SECOND_LEVEL_ID,
    ENTITY_METADATA_SECOND_LEVEL_ID,
    FEATURE_INFORMATION_SECOND_LEVEL_ID
)
from synesis_data_interface.structures.time_series.raw import TimeSeriesStructure
from synesis_data_interface.structures.base.validation import validate_feature_information


def validate_time_series_dataclass(data_structure: TimeSeriesStructure) -> None:
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
    validate_feature_information(
        feature_info_df, data_columns, TIME_SERIES_DATA_SECOND_LEVEL_ID, errors)

    if errors:
        raise ValueError(f"TimeSeries validation failed: {'; '.join(errors)}")
