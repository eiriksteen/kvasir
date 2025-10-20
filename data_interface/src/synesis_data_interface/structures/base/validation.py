import pandas as pd

from synesis_data_interface.structures.base.definitions import FEATURE_INFORMATION_SECOND_LEVEL_ID


def validate_feature_information(
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
