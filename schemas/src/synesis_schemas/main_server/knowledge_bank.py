from typing import List
from pydantic import field_validator
from pydantic import BaseModel

from .pipeline import FunctionWithoutEmbedding


KNOWLEDGE_BANK_MAX_K = 50


# API models

class SearchFunctionsRequest(BaseModel):
    queries: List[str]
    k: int

    @field_validator('k')
    def validate_k(cls, v):
        if v > KNOWLEDGE_BANK_MAX_K:
            raise ValueError(f"k must be less than {KNOWLEDGE_BANK_MAX_K}")
        return v


class SearchFunctionsResponse(BaseModel):
    functions: List[FunctionWithoutEmbedding]
