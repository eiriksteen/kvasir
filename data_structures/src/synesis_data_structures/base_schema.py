import uuid
from datetime import datetime, timedelta
from pydantic import BaseModel
from pydantic.alias_generators import to_camel
from typing import Optional, Dict, Any, Literal, Tuple, List


class BaseSchema(BaseModel):
    class Config:
        alias_generator = to_camel
        populate_by_name = True


# Schemas defining the structure of the data going in and out of the API
# Correspond to the outputs of data processing operations as sent through the API
# These types will be available at the frontend and will be plottable
# The agent provides corresponding outputs in the form of dataframes which are converted to these types
# An automation may lead to one or more of these types being returned
# The agent will have some frontend customization options to ensure these outputs are suitably displayed per user requirements
# DataObject is inherited in the models for specific modalities


class Feature(BaseSchema):
    name: str
    unit: str
    description: str
    type: Literal["numerical", "categorical"]
    subtype: Literal["continuous", "discrete"]
    scale: Literal["ratio", "interval", "ordinal", "nominal"]
    source: Literal["data", "metadata"]
    # For categorical features, we need to map the integer id to the label (None if feature is not categorical)
    category_id: Optional[int] = None


class DataObject(BaseSchema):
    id: uuid.UUID
    structure_type: Literal["time_series", "time_series_aggregation"]
    # Additional fields can be anything to accomodate for different use cases, for example metadata
    additional_variables: Optional[Dict[str, Any]] = None
    # feature name to feature object
    features: Dict[str, Feature]


class RawDataStructure(BaseSchema):
    data: Dict[Tuple[str, str], List[float | int | str | bool | datetime | timedelta | None]]  # (column_name, data_type) -> [values]

class AggregationOutput(BaseSchema):
    output_data: RawDataStructure