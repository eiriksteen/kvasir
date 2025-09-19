from typing import List, Dict, Any, Optional
from pydantic import BaseModel, field_validator

from synesis_schemas.main_server import FunctionInputStructureCreate, FunctionOutputStructureCreate, FunctionOutputVariableCreate
from synesis_schemas.main_server import SUPPORTED_MODALITIES_TYPE, SUPPORTED_TASK_TYPE


class ModelFunctionDescription(BaseModel):
    name: str
    description: str
    default_args: Dict[str, Any]
    input_structures: List[FunctionInputStructureCreate]
    output_structures: List[FunctionOutputStructureCreate]
    output_variables: List[FunctionOutputVariableCreate]


class ModelDescription(BaseModel):
    name: str
    description: str
    modality: SUPPORTED_MODALITIES_TYPE
    programming_language_with_version: str
    model_config: Dict[str, Any]
    task: SUPPORTED_TASK_TYPE
    training_function: ModelFunctionDescription
    inference_function: ModelFunctionDescription


class ImplementationFeedbackOutput(BaseModel):
    approved: bool
    feedback: Optional[str] = None

    @field_validator('feedback')
    @classmethod
    def validate_feedback_when_not_approved(cls, v, info):
        if not info.data.get('approved', True) and v is None:
            raise ValueError('Feedback is required when approved is False')
        return v
