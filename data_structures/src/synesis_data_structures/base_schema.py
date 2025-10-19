import uuid
from datetime import datetime, timedelta
from pydantic import BaseModel, Field
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


# description is included since an agent needs to know the json schema of the AggregationOutput (see prompt.py under analysis)
class Column(BaseSchema):
    name: str = Field(description="The name of the column.")
    value_type: Literal["float", "int", "str", "bool", "datetime", "timedelta", "None"] = Field(description="The type of the column. Should be one of the following: float, int, str, bool, datetime, timedelta, None.")
    values: List[float | int | str | bool | datetime | timedelta | None] = Field(description="The actual raw values stored in the the column.")

class RawDataStructure(BaseSchema):
    data: List[Column]

class AggregationOutput(BaseSchema):
    output_data: RawDataStructure