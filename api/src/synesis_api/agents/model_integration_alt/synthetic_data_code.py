TIME_SERIES_DUMMY_DATA_GENERATION_CODE = """
import numpy as np
import pandas as pd
from datetime import datetime, timedelta
import random

# Set random seed for reproducibility
np.random.seed(42)
random.seed(42)

# Constants
NUM_ENTITIES = 30
MIN_TIMESTAMPS = 1000
MAX_TIMESTAMPS = 3000
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
COUNTRIES = list(CITY_COUNTRY_MAP.values())
DISTRICTS = ['Downtown', 'Suburban', 'Industrial', 'Residential', 'Commercial']
ADMIN_CLASSES = ['national', 'provincial', 'municipal', 'village']

# Generate entity names (roads)
road_names = [f"Road_{i:03d}" for i in range(NUM_ENTITIES)]

# Generate timestamps (hourly data up to now)
end_time = datetime.now()
start_time = end_time - timedelta(hours=MAX_TIMESTAMPS)

# Create the time series data
all_data = []
all_entities = []
all_timestamps = []

for entity in road_names:
    # Random number of timestamps for this entity
    n_timestamps = random.randint(MIN_TIMESTAMPS, MAX_TIMESTAMPS)
    entity_timestamps = pd.date_range(
        end=end_time, periods=n_timestamps, freq='h')

    # Generate traffic data (cars per hour)
    # Base traffic level for this road
    base_traffic = np.random.randint(100, 1000)
    traffic = base_traffic + \
        np.random.normal(0, 100, n_timestamps)  # Add some noise
    traffic = np.maximum(0, traffic)  # Ensure non-negative
    traffic = traffic.astype(int)  # Convert to integer

    # Generate temperature data (in Celsius)
    base_temp = np.random.uniform(10, 25)  # Base temperature for this location
    # Add daily/seasonal variation
    temp = base_temp + np.random.normal(0, 5, n_timestamps)

    # Generate rain data (binary)
    # Different rain probabilities for different locations
    rain_prob = np.random.uniform(0.1, 0.3)
    rain = np.random.binomial(1, rain_prob, n_timestamps)

    # Combine all features
    entity_data = np.column_stack([traffic, temp, rain])

    all_data.append(entity_data)
    all_entities.extend([entity] * n_timestamps)
    all_timestamps.extend(entity_timestamps)

# Create the main time series DataFrame
miya_data = pd.DataFrame(
    np.vstack(all_data),
    index=pd.MultiIndex.from_arrays(
        [all_entities, all_timestamps],
        names=['entity', 'timestamp']
    ),
    columns=['cars_per_hour', 'temperature', 'is_raining']
)

# Create metadata
miya_metadata = pd.DataFrame({
    'city': np.random.choice(CITIES, NUM_ENTITIES),
    'district': np.random.choice(DISTRICTS, NUM_ENTITIES),
    'district_population': np.random.randint(10000, 1000000, NUM_ENTITIES),
    'city_population': np.random.randint(100000, 10000000, NUM_ENTITIES),
    'administrative_class': np.random.choice(ADMIN_CLASSES, NUM_ENTITIES)
}, index=road_names)
miya_metadata.index.name = 'entity'

# Map cities to their correct countries
miya_metadata['country'] = miya_metadata['city'].map(CITY_COUNTRY_MAP)

# Create miya_mapping for administrative_class
miya_mapping = {
    'administrative_class': {i: cls for i, cls in enumerate(ADMIN_CLASSES)}
}

# Convert administrative_class to integers
miya_metadata['administrative_class'] = miya_metadata['administrative_class'].map(
    {v: k for k, v in miya_mapping['administrative_class'].items()}
)

# Generate classification labels (accidents)
accident_labels = []
for entity in road_names:
    n_accidents = random.randint(5, 45)
    entity_data = miya_data.loc[entity]

    for _ in range(n_accidents):
        # Randomly select a timestamp for the accident
        accident_time = random.choice(entity_data.index)
        # Accident duration between 1 and 4 hours
        duration = random.randint(1, 4)

        accident_labels.append({
            'entity': entity,
            'start_timestamp': accident_time,
            'end_timestamp': accident_time + timedelta(hours=duration),
            'label': 1  # 1 indicates accident
        })

miya_labels = pd.DataFrame(accident_labels)

# Generate segmentation labels (traffic congestion levels)
segmentation_labels = []
for entity in road_names:
    entity_data = miya_data.loc[entity]
    traffic = entity_data['cars_per_hour']

    # Define congestion thresholds
    thresholds = {
        0: 0,      # Free flow
        1: 500,    # Mild congestion
        2: 800,    # Heavy congestion
        3: 1000    # Full stop
    }

    # Assign congestion levels based on traffic
    congestion_levels = np.zeros(len(traffic))
    for level, threshold in thresholds.items():
        congestion_levels[traffic >= threshold] = level

    # Create segmentation labels
    entity_segmentation = pd.DataFrame({
        'congestion_level': congestion_levels
    }, index=entity_data.index)
    entity_segmentation.index = pd.MultiIndex.from_arrays(
        [[entity] * len(traffic), entity_data.index],
        names=['entity', 'timestamp']
    )
    segmentation_labels.append(entity_segmentation)

miya_segmentation_labels = pd.concat(segmentation_labels)
"""

SYNTHETIC_BASE_CONFIG_CODE = f"""
base_config_dict = {{
    "num_features": 3,
    "seq_len": 96,
    "pred_len": 96,
    "label_len": 0,
    "categorical_columns": [],
    "categorical_columns_types": [],
    "continuous_columns": ["temperature"],
    "integer_columns": ["cars_per_hour"],
    "binary_columns": ["is_raining"],
    "metadata_categorical_columns": [
        'city', 'district', 'administrative_class', 'country'],
    "metadata_categorical_columns_types": [
        'string', 'string', 'string', 'string'],
    "metadata_continuous_columns": [],
    "metadata_integer_columns": [
        'district_population', 'city_population'],
    "metadata_binary_columns": [],
    "classification_classes": ['0', '1'],
    "segmentation_columns": ['congestion_level'],
    "segmentation_class_names_per_column": [
        ['Free flow', 'Mild congestion', 'Heavy congestion', 'Full stop']],
    "outer_index_name": 'entity',
    "inner_index_name": 'timestamp',
    "missing_values": False,
    "forecast_targets": ['cars_per_hour'],
    "input_features": ['cars_per_hour', 'temperature', 'is_raining'],
    "num_entities": 30,
    "min_entity_timestamps": 10000,
    "max_entity_timestamps": 30000,
    "mean_entity_timestamps": 20000,
    "total_num_timestamps": 600000,
    "num_epochs": 3,
    "batch_size": 32,
    "learning_rate": 0.001,
    "weight_decay": 0.0001
}}
"""


def get_synthetic_data(modality: str, task_name: str) -> dict:
    """
    Get the synthetic data code for a given modality and task.
    """
    if modality == "time_series":
        return TIME_SERIES_DUMMY_DATA_GENERATION_CODE
    else:
        raise ValueError(f"Modality {modality} not (yet) supported")


def get_synthetic_config() -> str:
    """
    Get the synthetic data code for a given modality and task.
    """

    # Assuming the Config class is already defined
    config_code = f"from config import Config\n\n{SYNTHETIC_BASE_CONFIG_CODE}\n\nconfig = Config(**base_config_dict)"
    return config_code
