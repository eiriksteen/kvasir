from pydantic import BaseModel
from typing import List, Literal


class CallSWEToImplementFunctionOutput(BaseModel):
    function_name: str
    function_description: str
    function_parameters: List[str]


class FeatureDescription(BaseModel):
    name: str
    unit: str
    description: str
    type: Literal["numerical", "categorical"]
    subtype: Literal["continuous", "discrete"]
    scale: Literal["ratio", "interval", "ordinal", "nominal"]


class TabularFileAnalysisOutput(BaseModel):
    file_size_bytes: int
    num_rows: int
    num_columns: int
    content_description: str
    quality_description: str
    eda_summary: str
    cautions: str
    features: List[FeatureDescription]
