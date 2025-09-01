from typing import List, Literal

from synesis_api.base_schema import BaseSchema


class FeatureDescription(BaseSchema):
    name: str
    unit: str
    description: str
    type: Literal["numerical", "categorical"]
    subtype: Literal["continuous", "discrete"]
    scale: Literal["ratio", "interval", "ordinal", "nominal"]


class DataSourceDescription(BaseSchema):
    source_name: str
    content_description: str
    quality_description: str
    num_rows: int
    features: List[FeatureDescription]


class DataSourceAnalysisAgentOutput(BaseSchema):
    data_sources: List[DataSourceDescription]
