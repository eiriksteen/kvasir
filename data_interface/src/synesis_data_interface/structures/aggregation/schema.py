from datetime import datetime, timedelta
from typing import List
from pydantic import BaseModel, Field
from typing import Literal

# description is included since an agent needs to know the json schema of the AggregationOutput (see prompt.py under analysis)


class Column(BaseModel):
    name: str = Field(description="The name of the column.")
    value_type: Literal["float", "int", "str", "bool", "datetime", "timedelta", "None"] = Field(
        description="The type of the column. Should be one of the following: float, int, str, bool, datetime, timedelta, None.")
    values: List[float | int | str | bool | datetime | timedelta | None] = Field(
        description="The actual raw values stored in the the column.")


class RawDataStructure(BaseModel):
    data: List[Column]


class AggregationOutput(BaseModel):
    output_data: RawDataStructure
