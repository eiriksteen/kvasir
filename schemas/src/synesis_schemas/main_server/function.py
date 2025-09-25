from pydantic import BaseModel
from typing import Optional, Literal, List
from datetime import datetime
from uuid import UUID


# DB models


class FunctionInDB(BaseModel):
    id: UUID
    name: str
    implementation_script_path: str
    created_at: datetime
    updated_at: datetime
    description: str
    embedding: List[float]
    type: Literal["inference", "training", "computation", "tool"]
    setup_script_path: Optional[str] = None
    default_args: Optional[dict] = None


class FunctionInputStructureInDB(BaseModel):
    id: UUID
    function_id: UUID
    structure_id: str
    name: str
    required: bool
    created_at: datetime
    updated_at: datetime
    description: Optional[str] = None


class FunctionOutputStructureInDB(BaseModel):
    id: UUID
    name: str
    function_id: UUID
    structure_id: str
    created_at: datetime
    updated_at: datetime
    description: Optional[str] = None


class FunctionOutputVariableInDB(BaseModel):
    id: UUID
    name: str
    function_id: UUID
    python_type: str
    created_at: datetime
    updated_at: datetime
    description: Optional[str] = None


# API models


class Function(FunctionInDB):
    input_structures: List[FunctionInputStructureInDB]
    output_structures: List[FunctionOutputStructureInDB]
    output_variables: List[FunctionOutputVariableInDB]


class FunctionBare(BaseModel):
    id: UUID
    name: str
    description: str
    input_structures: List[FunctionInputStructureInDB]
    output_structures: List[FunctionOutputStructureInDB]
    output_variables: List[FunctionOutputVariableInDB]
    default_args: Optional[dict] = None


# Create models


class FunctionOutputVariableCreate(BaseModel):
    name: str
    python_type: str
    description: Optional[str] = None


class FunctionInputStructureCreate(BaseModel):
    structure_id: str
    name: str
    description: str
    required: bool


class FunctionOutputStructureCreate(BaseModel):
    structure_id: str
    name: str
    description: str


class FunctionCreate(BaseModel):
    name: str
    description: str
    implementation_script_path: str
    type: Literal["inference", "training", "computation", "tool"]
    input_structures: List[FunctionInputStructureCreate]
    output_structures: List[FunctionOutputStructureCreate]
    output_variables: List[FunctionOutputVariableCreate]
    setup_script_path: Optional[str] = None
    default_args: Optional[dict] = None
