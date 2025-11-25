from pydantic import BaseModel, model_validator
from typing import Optional, Literal, List, Union
from datetime import datetime
from uuid import UUID


SUPPORTED_MODALITIES_TYPE = Literal["time_series", "tabular", "multimodal",
                                    "image", "text", "audio", "video"]


SUPPORTED_TASK_TYPE = Literal["forecasting", "classification", "regression",
                              "clustering", "anomaly_detection", "generation", "segmentation"]

FUNCTION_TYPE = Literal["training", "inference"]


SUPPORTED_MODEL_SOURCES_TYPE = Literal["github", "pypi"]

SUPPORTED_MODEL_SOURCES = ["github", "pypi"]


class ModelBase(BaseModel):
    id: UUID
    name: str
    user_id: UUID
    description: str
    created_at: datetime
    updated_at: datetime


class ModelImplementationBase(BaseModel):
    id: UUID  # Foreign key to model.id
    modality: SUPPORTED_MODALITIES_TYPE
    task: SUPPORTED_TASK_TYPE
    public: bool
    python_class_name: str
    source: SUPPORTED_MODEL_SOURCES_TYPE
    training_function_id: UUID
    inference_function_id: UUID
    implementation_script_path: str
    model_class_docstring: str
    default_config: dict
    config_schema: dict
    created_at: datetime
    updated_at: datetime


class ModelFunctionBase(BaseModel):
    id: UUID
    docstring: str
    args_schema: dict
    default_args: dict
    output_variables_schema: dict
    created_at: datetime
    updated_at: datetime


class ModelInstantiatedBase(BaseModel):
    id: UUID
    model_id: UUID
    user_id: UUID
    name: str
    description: str
    config: dict
    weights_save_dir: Optional[str] = None
    created_at: datetime
    updated_at: datetime


class ModelImplementation(ModelImplementationBase):
    training_function: ModelFunctionBase
    inference_function: ModelFunctionBase
    implementation_script_path: str


class Model(ModelBase):
    # None until implementation added (allows immediate UI update)
    implementation: Optional[ModelImplementation] = None


class ModelInstantiated(ModelInstantiatedBase):
    model: Model


# Create models


class ModelFunctionCreate(BaseModel):
    docstring: str
    args_schema: dict
    default_args: dict
    output_variables_schema: dict


class ModelImplementationCreate(BaseModel):
    python_class_name: str
    public: bool
    modality: SUPPORTED_MODALITIES_TYPE
    task: SUPPORTED_TASK_TYPE
    source: SUPPORTED_MODEL_SOURCES_TYPE
    model_class_docstring: str
    training_function: ModelFunctionCreate
    inference_function: ModelFunctionCreate
    default_config: dict
    config_schema: dict
    implementation_script_path: str
    model_id: UUID


class ModelCreate(BaseModel):
    name: str
    description: str
    implementation_create: Optional[ModelImplementationCreate] = None


class ModelInstantiatedCreate(BaseModel):
    name: str
    description: str
    config: dict
    weights_save_dir: Optional[str] = None
    model_create: Optional[ModelCreate] = None
    model_id: Optional[UUID] = None

    @model_validator(mode='after')
    def validate_model_specification(self):
        if self.model_id is None and self.model_create is None:
            raise ValueError(
                "Either model_id or model_create must be provided")
        return self
