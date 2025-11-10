from pydantic import BaseModel
from typing import Optional, Literal, List
from datetime import datetime
from uuid import UUID


# DB models


class FunctionDefinitionInDB(BaseModel):
    id: UUID
    name: str
    type: Literal["inference", "training", "computation", "tool"]
    args_dataclass_name: str
    input_dataclass_name: str
    output_dataclass_name: str
    output_variables_dataclass_name: str
    created_at: datetime
    updated_at: datetime


class FunctionInDB(BaseModel):
    id: UUID
    version: int
    python_function_name: str
    definition_id: UUID
    default_args: dict
    args_schema: dict
    output_variables_schema: dict
    newest_update_description: str
    implementation_script_path: str
    setup_script_path: Optional[str] = None
    docstring: str
    description: str
    embedding: List[float]
    created_at: datetime
    updated_at: datetime


# API models

# Merged function def and function
# We don't inherit since we want to drop the embedding field (could implement that differently but this works)
class FunctionWithoutEmbedding(BaseModel):
    id: UUID
    definition_id: UUID
    version: int
    args_schema: dict
    default_args: dict
    output_variables_schema: dict
    newest_update_description: str
    python_function_name: str
    implementation_script_path: str
    setup_script_path: Optional[str] = None
    docstring: str
    description: str
    created_at: datetime
    updated_at: datetime


class Function(FunctionWithoutEmbedding):
    definition: FunctionDefinitionInDB
    implementation_script_path: str
    setup_script_path: Optional[str] = None
    description_for_agent: str


class GetFunctionsRequest(BaseModel):
    function_ids: List[UUID]


# Create models


class FunctionCreate(BaseModel):
    name: str
    python_function_name: str
    docstring: str
    description: str
    args_schema: dict
    default_args: dict
    output_variables_schema: dict
    type: Literal["inference", "training", "computation", "tool"]
    args_dataclass_name: str
    input_dataclass_name: str
    output_dataclass_name: str
    output_variables_dataclass_name: str
    implementation_script_path: str
    setup_script_path: Optional[str] = None


class FunctionUpdateCreate(BaseModel):
    definition_id: UUID
    updates_made_description: str
    new_implementation_script_path: str
    new_setup_script_path: Optional[str] = None
    updated_python_function_name: Optional[str] = None
    updated_description: Optional[str] = None
    updated_docstring: Optional[str] = None
    updated_default_args: Optional[dict] = None
    updated_args_schema: Optional[dict] = None
    updated_output_variables_schema: Optional[dict] = None
