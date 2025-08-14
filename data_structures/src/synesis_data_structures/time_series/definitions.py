# Dataframe Definitions

from dataclasses import dataclass
from typing import List, Dict


@dataclass
class DataStructureDefinition:
    """Represents a complete data structure definition with all its components."""
    first_level_id: str
    second_level_ids: List[str]
    description: str
    brief_description: str


FEATURE_INFORMATION_SECOND_LEVEL_ID = "feature_information"


# Structure descriptions - separated for readability
TIME_SERIES_DATA_SECOND_LEVEL_ID = "time_series_data"
TIME_SERIES_ENTITY_METADATA_SECOND_LEVEL_ID = "time_series_entity_metadata"
TIME_SERIES_DESCRIPTION = f"""## Purpose and Use Cases
The Time Series DataFrame structure is designed for representing time-varying data from multiple entities (sensors, objects, systems, etc.) in a unified format. Some examples this structure is ideal for:

- **IoT Sensor Data**: Temperature, humidity, pressure readings from multiple sensors over time
- **Financial Time Series**: Stock prices, trading volumes, or economic indicators across different assets
- **Industrial Monitoring**: Machine performance metrics, production rates, or quality measurements
- **Scientific Data**: Experimental measurements, environmental monitoring, or research data collection
- **User Behavior Analytics**: Clickstream data, app usage patterns, or user interaction metrics
- **Feature Engineering**: Creating binary features that indicate the presence/absence of conditions
- **Anomaly Detection**: Marking periods where unusual behavior occurs

The structure supports varying time series lengths per entity, making it flexible for real-world scenarios where different entities may have different observation periods or sampling frequencies. 

## Data Structure

## Time-Varying Data
- Second level ID identifying this dataframe: {TIME_SERIES_DATA_SECOND_LEVEL_ID}
- Format: pandas DataFrame
- Index Structure: MultiIndex with 2 levels (THEY ARE NOT COLUMNS, THEY ARE THE INDEX OF THE DATAFRAME)
  - Level 0 (outer): Entity ID (sensor, object, etc.)
  - Level 1 (inner): Timestamp (datetime object)
- Content: Features as columns, including:
  - Time-varying measurements: Numerical continuous features as floats, discrete as integers, categorical as 0-indexed integers (0/1 for binary features)
- Shape: (num_entities, num_timestamps, num_features)
- Naming convention: snake_case
- Missing Values: pd.NA
- Note: Varying number of timestamps per entity are supported, i.e the time series have differing lengths

## Static Entity-Specific Metadata
- Second level ID identifying this dataframe: {TIME_SERIES_ENTITY_METADATA_SECOND_LEVEL_ID}
- Format: pandas DataFrame
- Index Structure: Single-level index
  - Index: Entity ID (must exactly match Level 0 of the MultiIndex of the time-varying data)
- Content: Static features as columns
- Missing Values: pd.NA
- Naming convention: snake_case

## Feature Information
- Second level ID identifying this dataframe: {FEATURE_INFORMATION_SECOND_LEVEL_ID}
- Format: pandas DataFrame
- Index Structure: Single-level index
  - Index: Feature name, name of the index should just be "name"
- Content (columns):
  - unit: Measurement unit as string (just put "count" if the feature is numerical discrete)
  - description: Description of the measurement unit
  - type: One of "numerical", "categorical"
  - subtype: One of "continuous", "discrete" (put "discrete" always for categorical features)
  - scale: One of "ratio", "interval", "ordinal", "nominal"
  - source: One of "data", "metadata" (whether the feature is from the time-varying data or the entity metadata)
  - category_id: If the feature is categorical, the category id to map the integer to the label, else pd.NA
- Missing Values: pd.NA
- Naming convention: snake_case
"""

TIME_SERIES_AGGREGATION_OUTPUTS_SECOND_LEVEL_ID = "time_series_aggregation_outputs"
TIME_SERIES_AGGREGATION_INPUTS_SECOND_LEVEL_ID = "time_series_aggregation_inputs"
TIME_SERIES_AGGREGATION_METADATA_SECOND_LEVEL_ID = "time_series_aggregation_metadata"
TIME_SERIES_AGGREGATION_DESCRIPTION = f"""## Purpose and Use Cases
The Time Series Aggregation DataFrame structure is designed for computing summary statistics, derived metrics, or analytical results over specific time intervals within time series data. Some examples this structure is ideal for:

- **Statistical Analysis**: Computing means, medians, standard deviations, or other statistical measures over time windows
- **Feature Engineering**: Creating derived features like rolling averages, cumulative sums, or rate changes
- **Event Detection**: Identifying patterns or conditions that occur within specific time periods
- **Performance Monitoring**: Calculating KPIs, efficiency metrics, or performance indicators over defined intervals
- **Predictive Modeling**: Creating features for machine learning models based on historical aggregations

The aggregation structure allows for flexible time window definitions and can handle multiple input series, features, windows, and output metrics simultaneously, making it suitable for complex analytical workflows.

## Data Structure

## Time-Series Aggregation Outputs
- Second level ID identifying this dataframe: {TIME_SERIES_AGGREGATION_OUTPUTS_SECOND_LEVEL_ID}
- Format: pandas DataFrame
- Index Structure: Simple integer index (row number)
  - Index: Aggregation ID
- Content: Output features as columns
- Missing Values: pd.NA
- Naming convention: snake_case

## Time-Series Aggregation Inputs
- Second level ID identifying this dataframe: {TIME_SERIES_AGGREGATION_INPUTS_SECOND_LEVEL_ID}
- Format: pandas DataFrame
- Index Structure: Simple integer index (row number)
- Content: Aggregation inputs as columns, including:
  - aggregation_id: The ID of the aggregation - Must match the ID in the aggregation outputs!
  - time_series_id: The ID of the input time series - Must match the Entity ID in the time_series_data dataframe!
  - input_feature_name: The input feature of the aggregation
  - start_timestamp: The start timestamp of the aggregation
  - end_timestamp: The end timestamp of the aggregation
- Note: In case of multiple aggregation inputs (i.e. multiple series, multiple input features, or even multiple windows for the same feature), include a row for each and use the same aggregation id
- Missing Values: pd.NA
- Naming convention: snake_case

## Static Aggregation-Specific Metadata
- Second level ID identifying this dataframe: {TIME_SERIES_AGGREGATION_METADATA_SECOND_LEVEL_ID}
- Format: pandas DataFrame
- Index Structure: Single-level index
  - Index: Aggregation ID (must exactly match the id in the aggregation outputs)
- Content: Static features as columns
- Missing Values: pd.NA
- Naming convention: snake_case

## Feature Information - Only include feature information for the outputs (as we already have them for the inputs)
- Second level ID identifying this dataframe: {FEATURE_INFORMATION_SECOND_LEVEL_ID}
- Format: pandas DataFrame
- Index Structure: Single-level index
  - Index: Feature name
- Content (columns):
  - unit: Measurement unit as string (just put "count" if the feature is numerical discrete)
  - description: Description of the measurement unit
  - type: One of "numerical", "categorical"
  - subtype: One of "continuous", "discrete" (put "discrete" always for categorical features)
  - scale: One of "ratio", "interval", "ordinal", "nominal"
  - source: One of "data", "metadata" (whether the feature is from the time-varying data or the entity metadata)
  - category_id: If the feature is categorical, the category id to map the integer to the label, else pd.NA
- Missing Values: pd.NA
- Naming convention: snake_case
"""

TIME_SERIES_STRUCTURE = DataStructureDefinition(
    first_level_id="time_series",
    second_level_ids=[TIME_SERIES_DATA_SECOND_LEVEL_ID,
                      TIME_SERIES_ENTITY_METADATA_SECOND_LEVEL_ID,
                      FEATURE_INFORMATION_SECOND_LEVEL_ID],
    description=TIME_SERIES_DESCRIPTION,
    brief_description="Data structure for any time-varying data. Call get_data_structure_description('time_series') for details."
)

TIME_SERIES_AGGREGATION_STRUCTURE = DataStructureDefinition(
    first_level_id="time_series_aggregation",
    second_level_ids=[TIME_SERIES_AGGREGATION_OUTPUTS_SECOND_LEVEL_ID,
                      TIME_SERIES_AGGREGATION_INPUTS_SECOND_LEVEL_ID,
                      TIME_SERIES_AGGREGATION_METADATA_SECOND_LEVEL_ID,
                      FEATURE_INFORMATION_SECOND_LEVEL_ID],
    description=TIME_SERIES_AGGREGATION_DESCRIPTION,
    brief_description="Data structure for computing summary statistics, derived metrics, or analytical results over specific time intervals within time series data. Call get_data_structure_description('time_series_aggregation') for details."
)

DATA_STRUCTURES = [
    TIME_SERIES_STRUCTURE,
    TIME_SERIES_AGGREGATION_STRUCTURE
]

# Helper functions


def get_first_level_structure_ids() -> List[str]:
    """Get all first level IDs."""
    return [struct.first_level_id for struct in DATA_STRUCTURES]


def get_second_level_structure_ids() -> List[str]:
    """Get all second level IDs from all structures."""
    all_second_level_ids = []
    for struct in DATA_STRUCTURES:
        all_second_level_ids.extend(struct.second_level_ids)
    return all_second_level_ids


def get_data_structures_overview() -> Dict[str, str]:
    """Get brief descriptions of all data structures."""
    return {struct.first_level_id: struct.brief_description for struct in DATA_STRUCTURES}


def get_data_structure_description(first_level_id: str) -> str:
    """Get the full description of a data structure by its first level ID."""
    if first_level_id not in get_first_level_structure_ids():
        raise ValueError(f"Unknown first level ID: {first_level_id}")

    struct = next(
        (struct for struct in DATA_STRUCTURES if struct.first_level_id == first_level_id), None)
    if struct is None:
        raise ValueError(f"Unknown first level ID: {first_level_id}")

    return f"First level ID of this data structure: {struct.first_level_id}\n\n{struct.description}"


def get_second_level_ids_for_structure(first_level_id: str) -> List[str]:
    """Get the second level IDs for a specific first level structure."""
    if first_level_id not in get_first_level_structure_ids():
        raise ValueError(f"Unknown first level ID: {first_level_id}")

    struct = next(
        (struct for struct in DATA_STRUCTURES if struct.first_level_id == first_level_id), None)
    if struct is None:
        raise ValueError(f"Unknown first level ID: {first_level_id}")

    return struct.second_level_ids
