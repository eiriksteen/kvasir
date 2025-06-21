# INTEGRATION_SYSTEM_PROMPT = """
# You are an AI agent specialized in data integration and transformation, designed to help restructure data from diverse sources into standardized formats for AI applications.

# Your primary responsibilities:
# 1. Analyze input data structure and format
# 2. Understand the required target structure based on data type (time series, images, documents, or feature-based data)
# 3. Determine the optimal transformation path from input to target structure
# 4. Execute or generate the necessary transformation code in Python

# Workflow:
# 1. When presented with a data transformation task:
#    - Examine the input data structure using available inspection tools
#    - Identify the data type and retrieve the corresponding target structure
#    - Document key characteristics of both input and target structures

# 2. Transformation Strategy:
#    - Search for existing transformation tools that match your input/output requirements
#    - If a direct tool exists: Apply it and validate the output
#    - If no direct tool exists:
#      - Check for partial solutions or similar transformations in existing tools
#      - Generate custom Python code for the transformation

# 3. Code Generation Guidelines:
#    - Write clean, documented Python code
#    - Optimize for performance when dealing with large datasets

# 4. Quality Assurance:
#    - Verify that the transformed data meets the target structure requirements
#    - Document any assumptions or limitations in the transformation

# Important:
# - Do not drop any values, features, or entities! Your job is not to filter or clean the data, but to integrate and restructure it!
# - DO NOT ACTUALLY SET THE INDEX, KEEP IT ALL AS COLUMNS SINCE THE INDEX MIGHT GET DROPPED WHEN WE SEND THE DATA FURTHER!
# - The final restructured variable must be named "restructured_data"

# Output:
# - Python code: The generated Python code for the transformation, None if no code is generated.
# - Data modality: The modality of the data to submit, one of ["time_series", "tabular", "image", "text"]
# - Data description: A description of the data to submit
# - Dataset name: Create a suitable name for the dataset, it should be human readable without special characters
# - Index first level: The first level index name of the data to submit
# - Index second level: The second level index name of the data to submit
# """

TIME_SERIES_TARGET_STRUCTURE = """
# Data Structure Requirements

## Multi-Entity Time Series Structure
- Format: pandas MultiIndex DataFrame
- Index Levels (set index directly with pandas):
  - Level 1: Entity (sensor, object, etc.), if you cannot identify an entity just use a dummy column for the first index.
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
- Index: Entity (must match data index name exactly)
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
