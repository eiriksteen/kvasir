from typing import List, Literal
from pydantic import field_validator
from pydantic import BaseModel

from synesis_schemas.main_server import Function, ModelImplementation


KNOWLEDGE_BANK_MAX_K = 30


# API models

class QueryRequest(BaseModel):
    query_name: str
    query: str
    k: int = 10

    @field_validator('k')
    def validate_k(cls, v):
        if v > KNOWLEDGE_BANK_MAX_K:
            raise ValueError(f"k must be less than {KNOWLEDGE_BANK_MAX_K}")
        return v


class SearchFunctionsRequest(BaseModel):
    queries: List[QueryRequest]


class FunctionQueryResult(BaseModel):
    query_name: str
    functions: List[Function]


class SearchModelsRequest(BaseModel):
    queries: List[QueryRequest]


class ModelQueryResult(BaseModel):
    query_name: str
    models: List[ModelImplementation]


class GetGuidelinesRequest(BaseModel):
    task: Literal["time_series_forecasting"]
