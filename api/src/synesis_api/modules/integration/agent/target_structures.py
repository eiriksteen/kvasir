TIME_SERIES_TARGET_STRUCTURE = """
# Data Structure Requirements

## Multi-Entity Time Series Structure
- Format: pandas MultiIndex DataFrame
- Index Levels (set index directly with pandas):
  - Level 1: Entity (sensor, object, etc.) - Must match metadata index name exactly!
  - Level 2: Timestamp (datetime object for datetime data, integer for non-datetime)
- Shape: (num_entities, num_timestamps, num_features)
- Note: Varying timesteps per entity are acceptable

## Single Entity Time Series Structure
- Format: pandas DataFrame
- Index: Timestamp (must be datetime object, set index directly with pandas)
- Shape: (num_timestamps, num_features)

# Metadata Processing Guidelines

## Time-Varying Metadata
- Categorical Features:
  - Convert to integers
  - Output mapping as "miya_mapping" dictionary
- Binary Features:
  - Convert to 0/1
  - Use descriptive variable names
- Missing Values:
  - Use pd.NA for unavailable features

## Static Metadata
- Format: pandas DataFrame named "miya_metadata"
- Index: Entity - Must match data index name exactly, apply renaming if necessary!
- Columns: Static features
- Missing Values: Use pd.NA
- Location Features:
  - City → "city"
  - Country → "country"
  - Other locations: Use snake_case

# Critical Rules
1. Data Preservation:
   - DO NOT drop important data
   - Preserve all metadata relevant for analysis/modeling
   - Separate time-varying (miya_data) and static (miya_metadata) data

2. Data Cleaning:
   - Drop only obviously uninformative columns (empty or redundant)
   - Maintain data integrity during transformations

3. Entity Selection:
   - Choose entities directly tied to time series
   - Each ID must correspond to a unique time series
   - For grouped entities, add group as column in entity_metadata

4. Data Inspection:
   - Thoroughly analyze input structure before transformation
   - Handle complex ID mappings carefully
   - Consider business context for data understanding
   - Validate all assumptions about data relationships
"""
