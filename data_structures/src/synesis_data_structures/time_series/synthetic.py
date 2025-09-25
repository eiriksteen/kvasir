import random
import pandas as pd
import numpy as np
from datetime import datetime
from typing import Union

from synesis_data_structures.time_series.definitions import (
    TIME_SERIES_DATA_SECOND_LEVEL_ID,
    TIME_SERIES_ENTITY_METADATA_SECOND_LEVEL_ID,
    FEATURE_INFORMATION_SECOND_LEVEL_ID,
    TIME_SERIES_AGGREGATION_OUTPUTS_SECOND_LEVEL_ID,
    TIME_SERIES_AGGREGATION_INPUTS_SECOND_LEVEL_ID,
    TIME_SERIES_AGGREGATION_METADATA_SECOND_LEVEL_ID
)
from synesis_data_structures.time_series.df_dataclasses import (
    TimeSeriesStructure,
    TimeSeriesAggregationStructure
)


def generate_synthetic_data(first_level_id: str) -> Union[TimeSeriesStructure, TimeSeriesAggregationStructure]:
    """
    Generate synthetic data for the specified first level structure.

    Args:
        first_level_id: The first level ID of the data structure ('time_series' or 'time_series_aggregation')

    Returns:
        A TimeSeriesStructure or TimeSeriesAggregationStructure instance
    """
    if first_level_id == "time_series":
        return _generate_synthetic_time_series_data()
    elif first_level_id == "time_series_aggregation":
        return _generate_synthetic_time_series_aggregation_data()
    else:
        raise ValueError(f"Unknown first level ID: {first_level_id}")


def _generate_synthetic_time_series_data(
    num_entities: int = 30,
    min_timestamps: int = 1000,
    max_timestamps: int = 3000,
    seed: int = 42
) -> TimeSeriesStructure:
    """
    Generate synthetic time series data following the new DataFrame structure.

    Returns a TimeSeriesStructure instance with:
    - time_series_data: MultiIndex DataFrame with entity and timestamp
    - time_series_entity_metadata: Entity-specific static metadata
    - feature_information: Feature descriptions and metadata
    """
    # Set random seed for reproducibility
    np.random.seed(seed)
    random.seed(seed)

    # Constants
    CITY_COUNTRY_MAP = {
        'New York': 'USA',
        'London': 'UK',
        'Tokyo': 'Japan',
        'Paris': 'France',
        'Berlin': 'Germany',
        'Sydney': 'Australia',
        'Singapore': 'Singapore',
        'Dubai': 'UAE',
        'Mumbai': 'India',
        'São Paulo': 'Brazil'
    }
    CITIES = list(CITY_COUNTRY_MAP.keys())
    DISTRICTS = ['Downtown', 'Suburban',
                 'Industrial', 'Residential', 'Commercial']
    ADMIN_CLASSES = ['national', 'provincial', 'municipal', 'village']

    # Generate entity names (roads)
    road_names = [f"Road_{i:03d}" for i in range(num_entities)]

    # Generate timestamps (hourly data up to now)
    end_time = datetime.now()

    # Create the time series data
    all_data = []
    all_entities = []
    all_timestamps = []

    for entity in road_names:
        # Random number of timestamps for this entity
        n_timestamps = random.randint(min_timestamps, max_timestamps)
        entity_timestamps = pd.date_range(
            end=end_time, periods=n_timestamps, freq='h')

        # Generate traffic data (cars per hour)
        base_traffic = np.random.randint(100, 1000)
        traffic = base_traffic + np.random.normal(0, 100, n_timestamps)
        traffic = np.maximum(0, traffic)
        traffic = traffic.astype(int)

        # Generate temperature data (in Celsius)
        base_temp = np.random.uniform(10, 25)
        temp = base_temp + np.random.normal(0, 5, n_timestamps)

        # Generate rain data (binary)
        rain_prob = np.random.uniform(0.1, 0.3)
        rain = np.random.binomial(1, rain_prob, n_timestamps)

        # Combine all features
        entity_data = np.column_stack([traffic, temp, rain])

        all_data.append(entity_data)
        all_entities.extend([entity] * n_timestamps)
        all_timestamps.extend(entity_timestamps)

    # Create the main time series DataFrame
    time_series_data = pd.DataFrame(
        np.vstack(all_data),
        index=pd.MultiIndex.from_arrays(
            [all_entities, all_timestamps],
            names=['entity', 'timestamp']
        ),
        columns=['cars_per_hour', 'temperature', 'is_raining']
    )

    # Create entity metadata
    time_series_entity_metadata = pd.DataFrame({
        'city': np.random.choice(CITIES, num_entities),
        'district': np.random.choice(DISTRICTS, num_entities),
        'district_population': np.random.randint(10000, 1000000, num_entities),
        'city_population': np.random.randint(100000, 10000000, num_entities),
        'administrative_class': np.random.choice(ADMIN_CLASSES, num_entities)
    }, index=road_names)
    time_series_entity_metadata.index.name = 'entity'

    # Map cities to their correct countries
    time_series_entity_metadata['country'] = time_series_entity_metadata['city'].map(
        CITY_COUNTRY_MAP)

    # Create mapping for administrative_class
    admin_mapping = {i: cls for i, cls in enumerate(ADMIN_CLASSES)}

    # Convert administrative_class to integers
    time_series_entity_metadata['administrative_class'] = time_series_entity_metadata['administrative_class'].map(
        {v: k for k, v in admin_mapping.items()}
    )

    # Create feature information
    feature_information = pd.DataFrame({
        'unit': ['cars/hour', 'celsius', 'count'],
        'description': [
            'Number of cars passing per hour',
            'Temperature in Celsius',
            'Binary indicator for rain (0=no rain, 1=rain)'
        ],
        'type': ['numerical', 'numerical', 'categorical'],
        'subtype': ['discrete', 'continuous', 'discrete'],
        'scale': ['ratio', 'interval', 'nominal'],
        'source': ['data', 'data', 'data'],
        'category_id': [pd.NA, pd.NA, 0]  # category_id 0 for rain mapping
    }, index=['cars_per_hour', 'temperature', 'is_raining'])
    feature_information.index.name = 'name'

    # Add metadata features to feature information
    metadata_features = pd.DataFrame({
        'unit': ['string', 'string', 'count', 'count', 'string', 'string'],
        'description': [
            'City name',
            'District name',
            'Population of the district',
            'Population of the city',
            'Administrative classification level',
            'Country name'
        ],
        'type': ['categorical', 'categorical', 'numerical', 'numerical', 'categorical', 'categorical'],
        'subtype': ['discrete', 'discrete', 'discrete', 'discrete', 'discrete', 'discrete'],
        'scale': ['nominal', 'nominal', 'ratio', 'ratio', 'nominal', 'nominal'],
        'source': ['metadata', 'metadata', 'metadata', 'metadata', 'metadata', 'metadata'],
        # Different category IDs for different categorical features
        'category_id': [1, 2, pd.NA, pd.NA, 3, 4]
    }, index=['city', 'district', 'district_population', 'city_population', 'administrative_class', 'country'])
    metadata_features.index.name = 'name'

    # Combine all feature information
    feature_information = pd.concat([feature_information, metadata_features])

    return TimeSeriesStructure(
        time_series_data=time_series_data,
        entity_metadata=time_series_entity_metadata,
        feature_information=feature_information
    )


def _generate_synthetic_time_series_aggregation_data(
    num_aggregations: int = 50,
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
    time_series_structure = _generate_synthetic_time_series_data(seed=seed)

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
