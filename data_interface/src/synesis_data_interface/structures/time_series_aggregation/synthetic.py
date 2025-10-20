import random
import pandas as pd
import numpy as np


from synesis_data_interface.structures.time_series_aggregation.raw import TimeSeriesAggregationStructure
from synesis_data_interface.structures.time_series.synthetic import generate_synthetic_time_series_data


TIME_SERIES_AGGREGATION_SYNTHETIC_DESCRIPTION = """# Synthetic Time Series Aggregation Data

Statistical aggregations computed over time windows of synthetic traffic data. 15 aggregations with variable windows (12+ hours).

## Aggregation Outputs (time_series_aggregation_outputs)
Indexed by aggregation_id with features based on input type:

**Traffic (cars_per_hour)**: mean_traffic, max_traffic, traffic_variance, peak_hour_traffic
**Temperature**: mean_temperature, temperature_range, temperature_std
**Rain (is_raining)**: total_rain_hours, rain_frequency, longest_rain_streak

## Aggregation Inputs (time_series_aggregation_inputs)
Columns: aggregation_id, time_series_id, input_feature_name, start_timestamp, end_timestamp

## Aggregation Metadata (entity_metadata)
Indexed by aggregation_id with columns:
- `aggregation_type`: Computation description
- `window_size_hours`: Time window duration
- `entity_city`: City location
- `entity_district`: District type

## Feature Information (feature_information)
Metadata for 11 output features with types, units, and descriptions.

Use cases: Statistical analysis, feature engineering, performance monitoring, automated reporting."""


def get_time_series_aggregation_synthetic_description() -> str:
    """Get description of the synthetic time series aggregation data."""
    return TIME_SERIES_AGGREGATION_SYNTHETIC_DESCRIPTION


def generate_synthetic_time_series_aggregation_data(
    num_aggregations: int = 15,
    seed: int = 42
) -> TimeSeriesAggregationStructure:
    """
    Generate synthetic time series aggregation data.
    This function internally generates time series data and then creates aggregations based on it.

    Args:
        num_aggregations: Number of aggregations to generate
        seed: Random seed for reproducibility

    Returns:
        A TimeSeriesAggregationStructure instance
    """
    # Set random seed
    np.random.seed(seed)
    random.seed(seed)

    # Generate the base time series data internally
    time_series_structure = generate_synthetic_time_series_data(seed=seed)

    # Extract the time series data
    ts_data = time_series_structure.time_series_data
    ts_metadata = time_series_structure.entity_metadata

    # Get unique entities and their data
    entities = ts_data.index.get_level_values('entity').unique()

    # Generate aggregation inputs
    aggregation_inputs = []
    aggregation_outputs = []
    aggregation_metadata = []

    for agg_id in range(num_aggregations):
        # Randomly select entity and feature
        entity = random.choice(entities)
        feature = random.choice(['cars_per_hour', 'temperature', 'is_raining'])

        # Get entity data
        entity_data = ts_data.loc[entity]

        # Generate random time window
        start_idx = random.randint(
            0, len(entity_data) - 24)  # At least 24 hours
        # At least 12 hours window
        end_idx = random.randint(start_idx + 12, len(entity_data))

        start_timestamp = entity_data.index[start_idx]
        end_timestamp = entity_data.index[end_idx]

        # Calculate aggregation based on feature type
        window_data = entity_data.iloc[start_idx:end_idx + 1][feature]

        if feature == 'cars_per_hour':
            # Calculate multiple statistics for traffic
            mean_traffic = window_data.mean()
            max_traffic = window_data.max()
            traffic_variance = window_data.var()
            peak_hour_traffic = window_data.quantile(0.95)

            # Add multiple outputs for this aggregation
            outputs = {
                'mean_traffic': mean_traffic,
                'max_traffic': max_traffic,
                'traffic_variance': traffic_variance,
                'peak_hour_traffic': peak_hour_traffic
            }

        elif feature == 'temperature':
            # Calculate temperature statistics
            mean_temp = window_data.mean()
            temp_range = window_data.max() - window_data.min()
            temp_std = window_data.std()

            outputs = {
                'mean_temperature': mean_temp,
                'temperature_range': temp_range,
                'temperature_std': temp_std
            }

        else:  # is_raining
            # Calculate rain statistics
            total_rain_hours = window_data.sum()
            rain_frequency = window_data.mean()
            longest_rain_streak = (window_data.astype(bool).astype(int).groupby(
                (window_data.astype(bool).astype(int) !=
                 window_data.astype(bool).astype(int).shift()).cumsum()
            ).sum().max())

            outputs = {
                'total_rain_hours': total_rain_hours,
                'rain_frequency': rain_frequency,
                'longest_rain_streak': longest_rain_streak
            }

        # Add aggregation inputs
        aggregation_inputs.append({
            'aggregation_id': agg_id,
            'time_series_id': entity,
            'input_feature_name': feature,
            'start_timestamp': start_timestamp,
            'end_timestamp': end_timestamp
        })

        # Add aggregation outputs
        for output_name, output_value in outputs.items():
            aggregation_outputs.append({
                'aggregation_id': agg_id,
                output_name: output_value
            })

        # Add aggregation metadata
        aggregation_metadata.append({
            'aggregation_id': agg_id,
            'aggregation_type': f'{feature}_statistics',
            'window_size_hours': (end_timestamp - start_timestamp).total_seconds() / 3600,
            'entity_city': ts_metadata.loc[entity, 'city'],
            'entity_district': ts_metadata.loc[entity, 'district']
        })

    # Create DataFrames
    aggregation_inputs_df = pd.DataFrame(aggregation_inputs)
    aggregation_outputs_df = pd.DataFrame(aggregation_outputs)
    aggregation_metadata_df = pd.DataFrame(aggregation_metadata)

    # Set index for outputs and metadata
    aggregation_outputs_df.set_index('aggregation_id', inplace=True)
    aggregation_metadata_df.set_index('aggregation_id', inplace=True)

    # Create feature information for aggregation outputs
    output_features = []

    # Traffic output features
    traffic_outputs = ['mean_traffic', 'max_traffic',
                       'traffic_variance', 'peak_hour_traffic']
    for feature in traffic_outputs:
        output_features.append({
            'name': feature,
            'unit': 'cars/hour',
            'description': f'{feature.replace("_", " ").title()} from traffic data aggregation',
            'type': 'numerical',
            'subtype': 'continuous',
            'scale': 'ratio',
            'source': 'data',
            'category_id': pd.NA
        })

    # Temperature output features
    temp_outputs = ['mean_temperature', 'temperature_range', 'temperature_std']
    for feature in temp_outputs:
        output_features.append({
            'name': feature,
            'unit': 'celsius',
            'description': f'{feature.replace("_", " ").title()} from temperature data aggregation',
            'type': 'numerical',
            'subtype': 'continuous',
            'scale': 'interval',
            'source': 'data',
            'category_id': pd.NA
        })

    # Rain output features
    rain_outputs = ['total_rain_hours',
                    'rain_frequency', 'longest_rain_streak']
    for feature in rain_outputs:
        unit = 'hours' if feature == 'total_rain_hours' else 'count'
        output_features.append({
            'name': feature,
            'unit': unit,
            'description': f'{feature.replace("_", " ").title()} from rain data aggregation',
            'type': 'numerical',
            'subtype': 'discrete',
            'scale': 'ratio',
            'source': 'data',
            'category_id': pd.NA
        })

    # Metadata features
    metadata_features = ['aggregation_type',
                         'window_size_hours', 'entity_city', 'entity_district']
    for feature in metadata_features:
        if feature == 'window_size_hours':
            output_features.append({
                'name': feature,
                'unit': 'hours',
                'description': 'Duration of the aggregation window',
                'type': 'numerical',
                'subtype': 'continuous',
                'scale': 'ratio',
                'source': 'metadata',
                'category_id': pd.NA
            })
        else:
            output_features.append({
                'name': feature,
                'unit': 'string',
                'description': f'{feature.replace("_", " ").title()} from aggregation metadata',
                'type': 'categorical',
                'subtype': 'discrete',
                'scale': 'nominal',
                'source': 'metadata',
                'category_id': 5  # New category ID for aggregation metadata
            })

    aggregation_feature_information = pd.DataFrame(output_features)
    aggregation_feature_information.set_index('name', inplace=True)

    return TimeSeriesAggregationStructure(
        time_series_aggregation_outputs=aggregation_outputs_df,
        time_series_aggregation_inputs=aggregation_inputs_df,
        entity_metadata=aggregation_metadata_df,
        feature_information=aggregation_feature_information
    )
