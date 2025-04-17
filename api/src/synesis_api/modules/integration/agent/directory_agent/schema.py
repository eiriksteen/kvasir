from uuid import UUID
from typing import Literal
from .....base_schema import BaseSchema


class IntegrationAgentOutput(BaseSchema):
    python_code: str
    # Currently only time series is supported
    data_modality: Literal["time_series"]
    data_description: str
    summary: str
    dataset_name: str
    dataset_id: UUID | None = None


class IntegrationAgentTimeSeriesOutput(IntegrationAgentOutput):
    index_first_level: str
    index_second_level: str | None
    data_modality: Literal["time_series"] = "time_series"
