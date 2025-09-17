from uuid import UUID
from datetime import datetime
from typing import Optional
from pydantic import BaseModel


# Defines the structure inputs of a function
class FunctionInputStructureInDB(BaseModel):
    id: UUID
    function_id: UUID
    structure_id: str
    name: str
    required: bool
    created_at: datetime
    updated_at: datetime
    description: Optional[str] = None


# Defines the structure outputs of a function
class FunctionOutputStructureInDB(BaseModel):
    id: UUID
    name: str
    function_id: UUID
    structure_id: str
    created_at: datetime
    updated_at: datetime
    description: Optional[str] = None


# Defines the variables outputs of a function
class FunctionOutputVariableInDB(BaseModel):
    id: UUID
    name: str
    function_id: UUID
    python_type: str
    created_at: datetime
    updated_at: datetime
    description: Optional[str] = None


# Defines the object group results of a pipeline run, both for inference and training
class PipelineRunObjectGroupResultInDB(BaseModel):
    id: UUID
    pipeline_run_id: UUID
    object_group_id: UUID
    created_at: datetime
    updated_at: datetime


# Defines the variables results of a training pipeline run (loss over epochs, feature importance, etc.)
class PipelineRunVariablesResultInDB(BaseModel):
    id: UUID
    pipeline_run_id: UUID
    variables_save_path: str
    created_at: datetime
    updated_at: datetime
