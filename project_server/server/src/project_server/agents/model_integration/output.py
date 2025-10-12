from typing import List, Dict, Any, Optional
from pydantic import BaseModel, field_validator

from synesis_schemas.main_server import ModelFunctionCreate
from synesis_schemas.main_server import SUPPORTED_MODALITIES_TYPE, SUPPORTED_TASK_TYPE


MAX_PYPI_QUERIES = 5


class SearchPypiPackagesOutput(BaseModel):
    package_names: List[str]

    @field_validator('package_names')
    @classmethod
    def validate_package_names(cls, v, info):
        if len(v) > MAX_PYPI_QUERIES:
            raise ValueError(
                f"Too many package names: {len(v)}, max is {MAX_PYPI_QUERIES}")
        return v


# TODO: Add outputs to search github as well


class ModelDescription(BaseModel):
    name: str
    python_class_name: str
    description: str
    modality: SUPPORTED_MODALITIES_TYPE
    task: SUPPORTED_TASK_TYPE
    programming_language_with_version: str
    model_class_docstring: str
    training_function: ModelFunctionCreate
    inference_function: ModelFunctionCreate
    default_config: dict
    config_schema: dict


class ImplementationFeedbackOutput(BaseModel):
    approved: bool
    feedback: Optional[str] = None

    @field_validator('feedback')
    @classmethod
    def validate_feedback_when_not_approved(cls, v, info):
        if not info.data.get('approved', True) and v is None:
            raise ValueError('Feedback is required when approved is False')
        return v
