#!/usr/bin/env python3
"""
Test script for synthetic data generation.
"""

from synesis_data_structures.time_series.definitions import (
    TIME_SERIES_DATA_SECOND_LEVEL_ID,
    TIME_SERIES_ENTITY_METADATA_SECOND_LEVEL_ID,
    FEATURE_INFORMATION_SECOND_LEVEL_ID,
    TIME_SERIES_AGGREGATION_OUTPUTS_SECOND_LEVEL_ID,
    TIME_SERIES_AGGREGATION_INPUTS_SECOND_LEVEL_ID,
    TIME_SERIES_AGGREGATION_METADATA_SECOND_LEVEL_ID
)
from synesis_data_structures.time_series.synthetic import (
    _generate_synthetic_time_series_data,
    _generate_synthetic_time_series_aggregation_data,
    generate_synthetic_data
)
import sys
import os
sys.path.insert(0, os.path.join(os.path.dirname(__file__), 'src'))


def test_time_series_generation():
    """Test time series data generation."""
    print("Testing time series data generation...")

    # Generate time series data
    time_series_data = _generate_synthetic_time_series_data(
        num_entities=5,
        min_timestamps=100,
        max_timestamps=200,
        seed=42
    )

    # Check that all required DataFrames are present
    required_keys = [
        TIME_SERIES_DATA_SECOND_LEVEL_ID,
        TIME_SERIES_ENTITY_METADATA_SECOND_LEVEL_ID,
        FEATURE_INFORMATION_SECOND_LEVEL_ID
    ]

    for key in required_keys:
        assert key in time_series_data, f"Missing key: {key}"
        print(f"✓ {key}: {time_series_data[key].shape}")

    # Check time series data structure
    ts_data = time_series_data[TIME_SERIES_DATA_SECOND_LEVEL_ID]
    assert isinstance(
        ts_data.index, pd.MultiIndex), "Time series data should have MultiIndex"
    assert list(ts_data.index.names) == [
        'entity', 'timestamp'], "Index names should be ['entity', 'timestamp']"
    assert list(ts_data.columns) == [
        'cars_per_hour', 'temperature', 'is_raining'], "Expected columns not found"

    # Check entity metadata
    ts_metadata = time_series_data[TIME_SERIES_ENTITY_METADATA_SECOND_LEVEL_ID]
    assert ts_metadata.index.name == 'entity', "Entity metadata should have 'entity' as index name"
    assert len(
        ts_metadata) == 5, f"Expected 5 entities, got {len(ts_metadata)}"

    # Check feature information
    feature_info = time_series_data[FEATURE_INFORMATION_SECOND_LEVEL_ID]
    assert feature_info.index.name == 'name', "Feature information should have 'name' as index name"

    print("✓ Time series data generation test passed!")
    return time_series_data


def test_aggregation_generation():
    """Test aggregation data generation."""
    print("\nTesting aggregation data generation...")

    # Generate aggregation data
    aggregation_data = _generate_synthetic_time_series_aggregation_data(
        num_aggregations=10,
        seed=42
    )

    # Check that all required DataFrames are present
    required_keys = [
        TIME_SERIES_AGGREGATION_OUTPUTS_SECOND_LEVEL_ID,
        TIME_SERIES_AGGREGATION_INPUTS_SECOND_LEVEL_ID,
        TIME_SERIES_AGGREGATION_METADATA_SECOND_LEVEL_ID,
        FEATURE_INFORMATION_SECOND_LEVEL_ID
    ]

    for key in required_keys:
        assert key in aggregation_data, f"Missing key: {key}"
        print(f"✓ {key}: {aggregation_data[key].shape}")

    # Check aggregation inputs
    agg_inputs = aggregation_data[TIME_SERIES_AGGREGATION_INPUTS_SECOND_LEVEL_ID]
    assert 'aggregation_id' in agg_inputs.columns, "Aggregation inputs should have 'aggregation_id' column"
    assert 'time_series_id' in agg_inputs.columns, "Aggregation inputs should have 'time_series_id' column"
    assert 'input_feature_name' in agg_inputs.columns, "Aggregation inputs should have 'input_feature_name' column"
    assert len(
        agg_inputs) == 10, f"Expected 10 aggregation inputs, got {len(agg_inputs)}"

    # Check aggregation outputs
    agg_outputs = aggregation_data[TIME_SERIES_AGGREGATION_OUTPUTS_SECOND_LEVEL_ID]
    assert agg_outputs.index.name == 'aggregation_id', "Aggregation outputs should have 'aggregation_id' as index"

    # Check aggregation metadata
    agg_metadata = aggregation_data[TIME_SERIES_AGGREGATION_METADATA_SECOND_LEVEL_ID]
    assert agg_metadata.index.name == 'aggregation_id', "Aggregation metadata should have 'aggregation_id' as index"
    assert len(
        agg_metadata) == 10, f"Expected 10 aggregation metadata entries, got {len(agg_metadata)}"

    print("✓ Aggregation data generation test passed!")
    return aggregation_data


def test_main_function():
    """Test the main generate_synthetic_data function."""
    print("\nTesting main generate_synthetic_data function...")

    # Test time series generation
    time_series_result = generate_synthetic_data("time_series")
    assert TIME_SERIES_DATA_SECOND_LEVEL_ID in time_series_result, "Time series result missing expected key"
    print("✓ Time series generation via main function passed!")

    # Test aggregation generation
    aggregation_result = generate_synthetic_data("time_series_aggregation")
    assert TIME_SERIES_AGGREGATION_OUTPUTS_SECOND_LEVEL_ID in aggregation_result, "Aggregation result missing expected key"
    print("✓ Aggregation generation via main function passed!")

    # Test invalid first level ID
    try:
        generate_synthetic_data("invalid_id")
        assert False, "Should have raised ValueError for invalid first level ID"
    except ValueError:
        print("✓ Invalid first level ID correctly raises ValueError")


def main():
    """Run all tests."""
    print("Running synthetic data generation tests...\n")

    # Test time series generation
    time_series_data = test_time_series_generation()

    # Test aggregation generation
    aggregation_data = test_aggregation_generation()

    # Test main function
    test_main_function()

    print("\n🎉 All tests passed!")


if __name__ == "__main__":
    import pandas as pd
    main()
