from uuid import UUID
from typing import Literal
from synesis_api.base_schema import BaseSchema


class ModelIntegrationJobInput(BaseSchema):
    model_id_str: str
    source: Literal["github", "pip", "source_code"]


class ModelIntegrationJobResult(BaseSchema):
    job_id: UUID
    model_id: UUID


class ModelIntegrationJobResultInDB(ModelIntegrationJobResult):
    pass
