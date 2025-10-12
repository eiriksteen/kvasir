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
    filename: str
    python_function_name: str
    definition_id: UUID
    default_args: dict
    args_schema: dict
    output_variables_schema: dict
    newest_update_description: str
    implementation_script_path: str
    module_path: str
    docstring: str
    description: str
    embedding: List[float]
    setup_script_path: Optional[str] = None
    created_at: datetime
    updated_at: datetime


class FunctionInputObjectGroupDefinitionInDB(BaseModel):
    id: UUID
    function_id: UUID
    structure_id: str
    name: str
    required: bool
    created_at: datetime
    updated_at: datetime
    description: str


class FunctionOutputObjectGroupDefinitionInDB(BaseModel):
    id: UUID
    name: str
    function_id: UUID
    structure_id: str
    output_entity_id_name: str
    created_at: datetime
    updated_at: datetime
    description: str


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
    filename: str
    module_path: str
    python_function_name: str
    implementation_script_path: str
    docstring: str
    description: str
    setup_script_path: Optional[str] = None
    created_at: datetime
    updated_at: datetime


class FunctionFull(FunctionWithoutEmbedding):
    definition: FunctionDefinitionInDB
    input_object_groups: List[FunctionInputObjectGroupDefinitionInDB]
    output_object_groups: List[FunctionOutputObjectGroupDefinitionInDB]


# Create models


class FunctionInputObjectGroupDefinitionCreate(BaseModel):
    structure_id: str
    name: str
    description: str
    required: bool


class FunctionOutputObjectGroupDefinitionCreate(BaseModel):
    structure_id: str
    name: str
    description: str
    output_entity_id_name: str


class FunctionCreate(BaseModel):
    name: str
    python_function_name: str
    docstring: str
    description: str
    filename: str
    module_path: str
    args_schema: dict
    default_args: dict
    output_variables_schema: dict
    implementation_script_path: str
    type: Literal["inference", "training", "computation", "tool"]
    args_dataclass_name: str
    input_dataclass_name: str
    output_dataclass_name: str
    output_variables_dataclass_name: str
    input_object_groups: List[FunctionInputObjectGroupDefinitionCreate]
    output_object_group_definitions: List[FunctionOutputObjectGroupDefinitionCreate]
    setup_script_path: Optional[str] = None


class FunctionUpdateCreate(BaseModel):
    definition_id: UUID
    updated_python_function_name: Optional[str] = None
    updates_made_description: str
    updated_description: Optional[str] = None
    updated_docstring: Optional[str] = None
    updated_setup_script_path: Optional[str] = None
    updated_default_args: Optional[dict] = None
    updated_args_schema: Optional[dict] = None
    updated_output_variables_schema: Optional[dict] = None
    updated_filename: Optional[str] = None
    updated_module_path: Optional[str] = None
    updated_implementation_script_path: Optional[str] = None
    input_object_groups_to_add: Optional[
        List[FunctionInputObjectGroupDefinitionCreate]] = None
    output_object_group_definitions_to_add: Optional[
        List[FunctionOutputObjectGroupDefinitionCreate]] = None
    input_object_groups_to_remove: Optional[List[UUID]] = None
    output_object_group_definitions_to_remove: Optional[List[UUID]] = None
