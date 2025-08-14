TIME_SERIES_INPUT_STRUCTURE = """
## Time-Varying Data
- Format: pandas DataFrame
- Name: "miya_data"
- Index Structure: MultiIndex with 2 levels (THEY ARE NOT COLUMNS, THEY ARE THE INDEX OF THE DATAFRAME)
  - Level 0 (outer): Entity (sensor, object, etc.)
  - Level 1 (inner): Timestamp (datetime object)
- Content: Features as columns, including:
  - Time-varying measurements
  - Time-varying metadata:
    - Categorical Features: Converted to integers
    - Binary Features: Converted to 0/1
    - Missing Values: pd.NA
- Shape: (num_entities, num_timestamps, num_features)
- Note: Varying number of timestamps per entity are supported, i.e the time series have differing lengths

## Static Metadata
- Format: pandas DataFrame
- Name: "miya_metadata"
- Index Structure: Single-level index
  - Index: Entity (must exactly match Level 0 of miya_data MultiIndex)
- Content: Static features as columns
- Missing Values: pd.NA
- Location Features:
  - City → "city"
  - Country → "country"
  - Other locations: snake_case

## Classification Labels
- Format: pandas DataFrame
- Name: "miya_labels"
- Index Structure: Simple integer index (row numbers)
- Columns:
  - entity: Entity identifier (must match Level 0 of miya_data MultiIndex)
  - start_timestamp: Start of labeled period
  - end_timestamp: End of labeled period
  - label: Categorical integer
- Missing Values: pd.NA
- Note: One entity can have multiple classifications, corresponding to different time periods

## Segmentation Labels
- Format: pandas DataFrame
- Name: "miya_segmentation_labels"
- Index Structure: MultiIndex with 2 levels (THEY ARE NOT COLUMNS, THEY ARE THE INDEX OF THE DATAFRAME)
  - Level 0 (outer): Entity (must exactly match Level 0 of miya_data MultiIndex)
  - Level 1 (inner): Timestamp (must match Level 1 of miya_data MultiIndex)
- Content: Features as columns (binary segmentation labels)
- Shape: (num_entities, num_timestamps, num_features)
- Note: Must align with miya_data timestamps

## Forecasting Labels
- For forecasting tasks, the past data in "miya_data" serves as the label
- Uses the same MultiIndex structure as Time-Varying Data

## Data Arguments
- Format: python dataclass object
- Name: "config"
- Content: Arguments for the input data
- Fields:
  - num_features: int
  - seq_len: Optional[int]
  - pred_len: Optional[int]
  - label_len: Optional[int]
  - categorical_columns: List[str]
  - categorical_columns_types: List[str]
  - continuous_columns: List[str]
  - integer_columns: List[str]
  - binary_columns: List[str]
  - metadata_categorical_columns: List[str]
  - metadata_categorical_columns_types: List[str]
  - metadata_continuous_columns: List[str]
  - metadata_integer_columns: List[str]
  - metadata_binary_columns: List[str]
  - classification_classes: List[str]
  - segmentation_columns: List[str]
  - segmentation_class_names_per_column: List[List[str]]
  - outer_index_name: str
  - inner_index_name: str
  - missing_values: bool
  - forecast_targets: List[str]
  - input_features: List[str]
  - num_entities: int
  - min_entity_timestamps: int
  - max_entity_timestamps: int
  - mean_entity_timestamps: int
  - total_num_timestamps: int
  - num_epochs: int
  - batch_size: int
  - learning_rate: float
  - weight_decay: float
  - [other parameters specific to the model, must be provided in the config_code]
"""


BASE_CONFIG_DEFINITION_CODE = """
from dataclasses import dataclass
from typing import List, Optional

@dataclass()
class BaseConfig:
    num_features: int
    seq_len: Optional[int]
    pred_len: Optional[int]
    label_len: Optional[int]
    categorical_columns: List[str]
    categorical_columns_types: List[str]
    continuous_columns: List[str]
    integer_columns: List[str]
    binary_columns: List[str]
    metadata_categorical_columns: List[str]
    metadata_categorical_columns_types: List[str]
    metadata_continuous_columns: List[str]
    metadata_integer_columns: List[str]
    metadata_binary_columns: List[str]
    classification_classes: List[str]
    segmentation_columns: List[str]
    segmentation_class_names_per_column: List[List[str]]
    outer_index_name: str
    inner_index_name: str
    missing_values: bool
    forecast_targets: List[str]
    input_features: List[str]
    num_entities: int
    min_entity_timestamps: int
    max_entity_timestamps: int
    mean_entity_timestamps: int
    total_num_timestamps: int
    num_epochs: int
    batch_size: int
    learning_rate: float
    weight_decay: float
"""


def get_input_structure(modality: str) -> str:
    if modality == "time_series":
        return TIME_SERIES_INPUT_STRUCTURE
    else:
        raise ValueError(f"Invalid modality: {modality}")


def get_config_definition_code() -> str:
    return BASE_CONFIG_DEFINITION_CODE
