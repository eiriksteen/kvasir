from synesis_data_interface.structures.base.definitions import FEATURE_INFORMATION_SECOND_LEVEL_ID, ENTITY_METADATA_SECOND_LEVEL_ID, DataStructureDefinition


# Structure descriptions
TIME_SERIES_FIRST_LEVEL_ID = "time_series"
TIME_SERIES_DATA_SECOND_LEVEL_ID = "time_series_data"
TIME_SERIES_DESCRIPTION = f"""# Description of the Kvasir structure: {TIME_SERIES_FIRST_LEVEL_ID}
The Time Series DataFrame structure is designed for representing time-varying data from multiple entities (sensors, objects, systems, etc.) in a unified format. Some examples this structure is ideal for:

- **IoT Sensor Data**: Temperature, humidity, pressure readings from multiple sensors over time
- **Financial Time Series**: Stock prices, trading volumes, or economic indicators across different assets
- **Industrial Monitoring**: Machine performance metrics, production rates, or quality measurements
- **Scientific Data**: Experimental measurements, environmental monitoring, or research data collection
- **User Behavior Analytics**: Clickstream data, app usage patterns, or user interaction metrics
- **Feature Engineering**: Creating binary features that indicate the presence/absence of conditions
- **Anomaly Detection**: Marking periods where unusual behavior occurs

The structure supports varying time series lengths per entity, making it flexible for real-world scenarios where different entities may have different observation periods or sampling frequencies. 

# Data Structure

## Time-Varying Data
- Second level ID identifying this dataframe: {TIME_SERIES_DATA_SECOND_LEVEL_ID}
- Format: pandas DataFrame
- Index Structure: MultiIndex with 2 levels (THEY ARE NOT COLUMNS, THEY ARE THE INDEX OF THE DATAFRAME)
  - Level 0 (outer): Entity ID (sensor, object, etc.)
  - Level 1 (inner): Timestamp (datetime object - Timezone aware!)
- Content: Features as columns, including:
  - Time-varying measurements: Numerical continuous features as floats, discrete as integers, categorical as 0-indexed integers (0/1 for binary features)
- Shape: (num_entities, num_timestamps, num_features)
- Missing Values: pd.NA
- Note: Varying number of timestamps per entity are supported, i.e the time series have differing lengths

## Static Entity-Specific Metadata
- Second level ID identifying this dataframe: {ENTITY_METADATA_SECOND_LEVEL_ID}
- Format: pandas DataFrame
- Index Structure: Single-level index
  - Index: Entity ID (must exactly match Level 0 of the MultiIndex of the time-varying data)
- Content: Static features as columns
  - Fixed columns (always present):
    - num_timestamps: Number of timestamps for the entity time series
    - start_timestamp: Start timestamp of the entity time series
    - end_timestamp: End timestamp of the entity time series
    - sampling_frequency: Sampling frequency of the entity time series - Must be one of 'm', 'h', 'd', 'w', 'y' or 'irr'
    - timezone: Timezone of the entity time series
  - Variable columns:
    - Any other column may be defined which is specific to the entity
- Missing Values: pd.NA

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

# Access in your code

Note: This is mainly relevant for accessing existing datasets. When creating a new one, the prompt will tell you the desired output.

The time-varying data, entity metadata, and feature information together encompass a time series group. 
The following dataclass will be defined for you, and it lets you access the dataframes in a group.
If you need to access the definition, you can import it with 'from synesis_data_interface.structures.time_series.raw import TimeSeriesStructure'.

@dataclass
class TimeSeriesStructure:
    {TIME_SERIES_DATA_SECOND_LEVEL_ID}: pd.DataFrame
    {ENTITY_METADATA_SECOND_LEVEL_ID}: pd.DataFrame
    {FEATURE_INFORMATION_SECOND_LEVEL_ID}: pd.DataFrame

Note that the entity metadata and feature information dataframes are required, and they must be non-empty. 
The entity metadata must containe at minimum the columns described above. 
The feature information must also be populated, as every feature in the time series data must be described in the feature information.

If relevant, the name(s) of the instantiated TimeSeriesStructure(s) will be provided to you, so you can access the data in your code. 
"""

TIME_SERIES_STRUCTURE = DataStructureDefinition(
    first_level_id=TIME_SERIES_FIRST_LEVEL_ID,
    second_level_ids=[TIME_SERIES_DATA_SECOND_LEVEL_ID,
                      ENTITY_METADATA_SECOND_LEVEL_ID,
                      FEATURE_INFORMATION_SECOND_LEVEL_ID],
    description=TIME_SERIES_DESCRIPTION,
    brief_description="Data structure for any time-varying data. Call get_data_structure_description('time_series') for details."
)
