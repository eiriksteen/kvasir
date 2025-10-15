from pydantic import BaseModel
from datetime import datetime
from uuid import UUID
from typing import Literal, Optional

# DB Models

script_type_literal = Literal["function", "model", "pipeline",
                              "data_integration", "analysis"]


class ScriptInDB(BaseModel):
    id: UUID
    user_id: UUID
    path: str
    filename: str
    module_path: str
    type: script_type_literal
    output: Optional[str] = None
    error: Optional[str] = None
    created_at: datetime
    updated_at: datetime


# Create models

class ScriptCreate(BaseModel):
    path: str
    filename: str
    module_path: str
    type: script_type_literal
    output: Optional[str] = None
    error: Optional[str] = None
