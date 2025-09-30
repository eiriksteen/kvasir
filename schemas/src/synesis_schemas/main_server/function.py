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
    definition_id: UUID
    version: int
    implementation_script_path: str
    description: str
    embedding: List[float]
    setup_script_path: Optional[str] = None
    default_args_dict: Optional[dict] = None
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
    description: Optional[str] = None


class FunctionOutputObjectGroupDefinitionInDB(BaseModel):
    id: UUID
    name: str
    function_id: UUID
    structure_id: str
    created_at: datetime
    updated_at: datetime
    description: Optional[str] = None


class FunctionOutputVariableDefinitionInDB(BaseModel):
    id: UUID
    name: str
    function_id: UUID
    python_type: str
    created_at: datetime
    updated_at: datetime
    description: Optional[str] = None


# API models

# Merged function def and function
# We don't inherit since we want to drop the embedding field (could implement that differently but this works)
class FunctionBare(BaseModel):
    id: UUID
    definition_id: UUID
    name: str
    type: Literal["inference", "training", "computation", "tool"]
    args_dataclass_name: str
    input_dataclass_name: str
    output_dataclass_name: str
    output_variables_dataclass_name: str
    version: int
    implementation_script_path: str
    description: str
    setup_script_path: Optional[str] = None
    default_args_dict: Optional[dict] = None
    input_object_groups: List[FunctionInputObjectGroupDefinitionInDB]
    output_object_groups: List[FunctionOutputObjectGroupDefinitionInDB]
    output_variables: List[FunctionOutputVariableDefinitionInDB]
    created_at: datetime
    updated_at: datetime


# Create models


class FunctionOutputVariableDefinitionCreate(BaseModel):
    name: str
    python_type: str
    description: Optional[str] = None


class FunctionInputObjectGroupDefinitionCreate(BaseModel):
    structure_id: str
    name: str
    description: str
    required: bool


class FunctionOutputObjectGroupDefinitionCreate(BaseModel):
    structure_id: str
    name: str
    description: str


class FunctionCreate(BaseModel):
    name: str
    description: str
    implementation_script_path: str
    type: Literal["inference", "training", "computation", "tool"]
    args_dataclass_name: str
    input_dataclass_name: str
    output_dataclass_name: str
    output_variables_dataclass_name: str
    input_object_group_descriptions: List[FunctionInputObjectGroupDefinitionCreate]
    output_object_group_descriptions: List[FunctionOutputObjectGroupDefinitionCreate]
    output_variables_descriptions: List[FunctionOutputVariableDefinitionCreate]
    setup_script_path: Optional[str] = None
    default_args_dict: Optional[dict] = None


class FunctionUpdateCreate(BaseModel):
    definition_id: UUID
    updated_description: Optional[str] = None
    updated_setup_script_path: Optional[str] = None
    updated_default_args_dict: Optional[dict] = None
    updated_implementation_script_path: Optional[str] = None
    input_object_group_descriptions_to_add: Optional[
        List[FunctionInputObjectGroupDefinitionCreate]] = None
    output_object_group_descriptions_to_add: Optional[
        List[FunctionOutputObjectGroupDefinitionCreate]] = None
    output_variables_descriptions_to_add: Optional[List[FunctionOutputVariableDefinitionCreate]] = None
    input_object_group_descriptions_to_remove: Optional[List[UUID]] = None
    output_object_group_descriptions_to_remove: Optional[List[UUID]] = None
    output_variables_descriptions_to_remove: Optional[List[UUID]] = None
