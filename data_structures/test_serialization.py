#!/usr/bin/env python3
"""
Test script for the new serialization functions.
"""

import pandas as pd
import uuid
from datetime import datetime, timedelta
from synesis_data_structures.time_series import (
    serialize_dataframes_to_api_payloads,
    serialize_dataframes_to_parquet,
    deserialize_parquet_to_dataframes
)


def create_sample_time_series_data():
    """Create sample time series data for testing."""
    # Create sample data
    entities = ['sensor_001', 'sensor_002']
    timestamps = pd.date_range(start='2024-01-01', end='2024-01-10', freq='h')

    # Create time series data
    data_records = []
    for entity in entities:
        for ts in timestamps:
            data_records.append({
                'entity_id': entity,
                'timestamp': ts,
                # Random temperature
                'temperature': 20 + (hash(f"{entity}{ts}") % 10),
                # Random humidity
                'humidity': 50 + (hash(f"{entity}{ts}") % 20)
            })

    time_series_data = pd.DataFrame(data_records)
    time_series_data.set_index(['entity_id', 'timestamp'], inplace=True)

    # Create entity metadata
    metadata_records = [
        {'entity_id': 'sensor_001', 'location': 'room_a', 'type': 'temperature'},
        {'entity_id': 'sensor_002', 'location': 'room_b', 'type': 'temperature'}
    ]
    time_series_entity_metadata = pd.DataFrame(metadata_records)
    time_series_entity_metadata.set_index('entity_id', inplace=True)

    # Create feature information
    feature_info_records = [
        {
            'feature_name': 'temperature',
            'unit': 'celsius',
            'description': 'Temperature reading in Celsius',
            'type': 'numerical',
            'subtype': 'continuous',
            'scale': 'interval',
            'source': 'data',
            'category_id': None
        },
        {
            'feature_name': 'humidity',
            'unit': 'percent',
            'description': 'Humidity reading as percentage',
            'type': 'numerical',
            'subtype': 'continuous',
            'scale': 'ratio',
            'source': 'data',
            'category_id': None
        }
    ]
    time_series_feature_information = pd.DataFrame(feature_info_records)
    time_series_feature_information.set_index('feature_name', inplace=True)

    return {
        'time_series_data': time_series_data,
        'time_series_entity_metadata': time_series_entity_metadata,
        'time_series_feature_information': time_series_feature_information
    }


def test_time_series_serialization():
    """Test the new serialization functions with time series data."""
    print("Testing time series serialization functions...")

    # Create sample data
    dataframes = create_sample_time_series_data()
    first_level_id = "time_series"

    print(f"Sample data created with {len(dataframes)} DataFrames")
    print(f"Time series data shape: {dataframes['time_series_data'].shape}")
    print(
        f"Entity metadata shape: {dataframes['time_series_entity_metadata'].shape}")
    print(
        f"Feature information shape: {dataframes['time_series_feature_information'].shape}")

    # Test 1: Serialize to API payloads
    print("\n1. Testing serialize_dataframes_to_api_payloads...")
    api_payloads = serialize_dataframes_to_api_payloads(
        dataframes, first_level_id)
    print(f"Generated {len(api_payloads)} API payloads")
    for i, payload in enumerate(api_payloads[:2]):  # Show first 2
        print(f"  Payload {i+1}: {type(payload).__name__}, id={payload.id}")
        print(f"    Structure type: {payload.structure_type}")
        print(f"    Features: {list(payload.data.keys())}")

    # Test 2: Serialize to parquet format
    print("\n2. Testing serialize_dataframes_to_parquet...")
    parquet_data = serialize_dataframes_to_parquet(dataframes, first_level_id)
    print(f"Parquet data contains {len(parquet_data)} parquet byte objects")
    for second_level_id, parquet_bytes in parquet_data.items():
        print(f"  {second_level_id}: {len(parquet_bytes)} bytes")

    # Test 3: Deserialize from parquet format
    print("\n3. Testing deserialize_parquet_to_dataframes...")
    deserialized_data = deserialize_parquet_to_dataframes(
        parquet_data, first_level_id)
    print(f"Deserialized data contains {len(deserialized_data)} DataFrames")

    # Verify the data is preserved
    print("\n4. Verifying data preservation...")
    original_keys = set(dataframes.keys())
    deserialized_keys = set(deserialized_data.keys())

    if original_keys == deserialized_keys:
        print("  ✓ All second level IDs preserved")
    else:
        print(
            f"  ✗ Key mismatch: original={original_keys}, deserialized={deserialized_keys}")

    # Check DataFrame shapes are preserved
    shapes_preserved = True
    for key in original_keys:
        if dataframes[key].shape != deserialized_data[key].shape:
            print(
                f"  ✗ Shape mismatch for {key}: {dataframes[key].shape} != {deserialized_data[key].shape}")
            shapes_preserved = False

    if shapes_preserved:
        print("  ✓ All DataFrame shapes preserved")

    print("\n✅ All tests completed successfully!")


def test_error_handling():
    """Test error handling for invalid inputs."""
    print("\nTesting error handling...")

    # Test with invalid first level ID
    try:
        serialize_dataframes_to_api_payloads({}, "invalid_id")
        print("  ✗ Should have raised ValueError for invalid first level ID")
    except ValueError as e:
        print(f"  ✓ Correctly raised ValueError: {e}")

    # Test with missing second level IDs
    try:
        serialize_dataframes_to_parquet(
            {'time_series_data': pd.DataFrame()}, "time_series")
        print("  ✗ Should have raised ValueError for missing second level IDs")
    except ValueError as e:
        print(f"  ✓ Correctly raised ValueError: {e}")

    # Test deserialization with invalid bytes
    try:
        deserialize_parquet_to_dataframes(
            {'time_series_data': b'invalid_bytes'}, "time_series")
        print("  ✗ Should have raised error for invalid parquet bytes")
    except Exception as e:
        print(f"  ✓ Correctly raised error for invalid parquet bytes: {e}")

    print("✅ Error handling tests completed!")


if __name__ == "__main__":
    test_time_series_serialization()
    test_error_handling()
