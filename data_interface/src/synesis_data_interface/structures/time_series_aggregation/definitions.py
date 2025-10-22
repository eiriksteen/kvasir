from synesis_data_interface.structures.base.definitions import FEATURE_INFORMATION_SECOND_LEVEL_ID, ENTITY_METADATA_SECOND_LEVEL_ID, DataStructureDefinition


TIME_SERIES_AGGREGATION_FIRST_LEVEL_ID = "time_series_aggregation"
TIME_SERIES_AGGREGATION_OUTPUTS_SECOND_LEVEL_ID = "time_series_aggregation_outputs"
TIME_SERIES_AGGREGATION_INPUTS_SECOND_LEVEL_ID = "time_series_aggregation_inputs"
TIME_SERIES_AGGREGATION_DESCRIPTION = f"""# Description of the Kvasir structure: {TIME_SERIES_AGGREGATION_FIRST_LEVEL_ID}
The Time Series Aggregation DataFrame structure is designed for computing summary statistics, derived metrics, or analytical results over specific time intervals within time series data. Some examples this structure is ideal for:

- **Statistical Analysis**: Computing means, medians, standard deviations, or other statistical measures over time windows
- **Feature Engineering**: Creating derived features like rolling averages, cumulative sums, or rate changes
- **Event Detection**: Identifying patterns or conditions that occur within specific time periods
- **Performance Monitoring**: Calculating KPIs, efficiency metrics, or performance indicators over defined intervals
- **Predictive Modeling**: Creating features for machine learning models based on historical aggregations

The aggregation structure allows for flexible time window definitions and can handle multiple input series, features, windows, and output metrics simultaneously, making it suitable for complex analytical workflows.

NB: It should NOT be used to store arbitrary output values, such as loss values or other metrics. It is used to store the outputs of computations on slices in the series! Use output variables to store arbitrary outputs and metrics. 
DO NOT USE TIME SERIES AGGREGATION TO STORE METRICS OR LOSS VALUES!  

## Data Structure

## Time-Series Aggregation Outputs
- Second level ID identifying this dataframe: {TIME_SERIES_AGGREGATION_OUTPUTS_SECOND_LEVEL_ID}
- Format: pandas DataFrame
- Index Structure: Simple integer index (row number)
  - Index: Aggregation ID
- Content: Output features as columns
- Missing Values: pd.NA

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

## Static Aggregation-Specific Metadata
- Second level ID identifying this dataframe: {ENTITY_METADATA_SECOND_LEVEL_ID}
- Format: pandas DataFrame
- Index Structure: Single-level index
  - Index: Aggregation ID (must exactly match the id in the aggregation outputs)
- Content: Static features as columns
  - Fixed columns (always present):
    - is_multi_series_computation: Whether the aggregation is computed from multiple time series
  - Variable columns:
    - Any other column may be defined which is specific to the aggregation
- Missing Values: pd.NA

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

# Access in your code

Note: This is mainly relevant for accessing existing datasets. When creating a new one, the prompt will tell you the desired output.

The aggregation outputs, inputs, aggregation metadata, and feature information together encompass a time series aggregation group. 
The following dataclass will be defined for you, and it lets you access the dataframes in a group.
If you need to access the definition, you can import it with 'from synesis_data_interface.structures.time_series.raw import TimeSeriesAggregationStructure'.

@dataclass
class TimeSeriesAggregationStructure:
    {TIME_SERIES_AGGREGATION_OUTPUTS_SECOND_LEVEL_ID}: pd.DataFrame
    {TIME_SERIES_AGGREGATION_INPUTS_SECOND_LEVEL_ID}: pd.DataFrame
    {ENTITY_METADATA_SECOND_LEVEL_ID}: pd.DataFrame
    {FEATURE_INFORMATION_SECOND_LEVEL_ID}: pd.DataFrame
    
Note that the entity metadata and feature information dataframes are required, and they must be non-empty. 
The entity metadata must containe at minimum the columns described above. 
The feature information must also be populated, as every feature in the time series data must be described in the feature information.

If relevant, the name(s) of the instantiated TimeSeriesAggregationStructure(s) will be provided to you, so you can access the data in your code. 
"""


TIME_SERIES_AGGREGATION_STRUCTURE = DataStructureDefinition(
    first_level_id=TIME_SERIES_AGGREGATION_FIRST_LEVEL_ID,
    second_level_ids=[TIME_SERIES_AGGREGATION_OUTPUTS_SECOND_LEVEL_ID,
                      TIME_SERIES_AGGREGATION_INPUTS_SECOND_LEVEL_ID,
                      ENTITY_METADATA_SECOND_LEVEL_ID,
                      FEATURE_INFORMATION_SECOND_LEVEL_ID],
    description=TIME_SERIES_AGGREGATION_DESCRIPTION,
    brief_description="Data structure for computing summary statistics, derived metrics, or analytical results over specific time intervals within time series data. Call get_data_structure_description('time_series_aggregation') for details."
)
