import uuid
from synesis_api.base_schema import BaseSchema


class DataIntegrationAgentOutput(BaseSchema):
    summary: str
    code_explanation: str
    code: str


class DataIntegrationAgentOutputWithDatasetId(DataIntegrationAgentOutput):
    dataset_id: uuid.UUID
