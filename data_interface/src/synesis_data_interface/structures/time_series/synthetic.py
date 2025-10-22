import random
import pandas as pd
import numpy as np
from datetime import datetime

from synesis_data_interface.structures.time_series.raw import TimeSeriesStructure

# Synthetic data descriptions
TIME_SERIES_SYNTHETIC_DESCRIPTION = """# Synthetic Time Series Data

Simulates traffic monitoring from 5 road sensors across cities. Variable-length time series (400-600 hourly observations) ending at current timestamp.

## Time-Varying Data (time_series_data)
MultiIndex DataFrame (entity, timestamp) with columns:
- `cars_per_hour` (int): Traffic count (0-1200, normally distributed)
- `temperature` (float): Celsius temperature (10-25°C mean ±5°C variation)
- `is_raining` (int): Binary rain indicator (10-30% probability)

## Entity Metadata (entity_metadata)
Indexed by entity ID with columns:
- `city`: City name (10 major cities: NY, London, Tokyo, Paris, Berlin, Sydney, Singapore, Dubai, Mumbai, São Paulo)
- `district`: District type (Downtown, Suburban, Industrial, Residential, Commercial)
- `district_population`: Population (10K-1M)
- `city_population`: Population (100K-10M)
- `administrative_class`: Level (0=national, 1=provincial, 2=municipal, 3=village)
- `country`: Corresponding country

## Feature Information (feature_information)
Metadata for 9 features (3 time-varying + 6 static) with units, types, and categorical mappings.

Use cases: Traffic analysis, weather impact studies, urban planning, sensor testing, anomaly detection."""


def get_time_series_synthetic_description() -> str:
    """Get description of the synthetic time series data."""
    return TIME_SERIES_SYNTHETIC_DESCRIPTION


def generate_synthetic_time_series_data(
    num_entities: int = 5,
    min_timestamps: int = 400,
    max_timestamps: int = 600,
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
