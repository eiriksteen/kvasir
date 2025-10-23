from pydantic import BaseModel, model_validator
from typing import Optional, Literal, List, Union
from datetime import datetime
from uuid import UUID


from .code import ScriptCreate, ScriptInDB


SUPPORTED_MODALITIES_TYPE = Literal["time_series", "tabular", "multimodal",
                                    "image", "text", "audio", "video"]


SUPPORTED_TASK_TYPE = Literal["forecasting", "classification", "regression",
                              "clustering", "anomaly_detection", "generation", "segmentation"]

FUNCTION_TYPE = Literal["training", "inference"]


SUPPORTED_MODEL_SOURCES_TYPE = Literal["github", "pypi"]

SUPPORTED_MODEL_SOURCES = ["github", "pypi"]


# DB models

class ModelDefinitionInDB(BaseModel):
    id: UUID
    name: str
    modality: SUPPORTED_MODALITIES_TYPE
    task: SUPPORTED_TASK_TYPE
    public: bool
    created_at: datetime
    updated_at: datetime


class ModelImplementationInDB(BaseModel):
    id: UUID
    definition_id: UUID
    version: int
    python_class_name: str
    description: str
    newest_update_description: str
    user_id: UUID
    source_id: UUID
    embedding: List[float]
    implementation_script_id: UUID
    setup_script_id: Optional[UUID] = None
    model_class_docstring: str
    default_config: dict
    config_schema: dict
    training_function_id: UUID
    inference_function_id: UUID
    created_at: datetime
    updated_at: datetime


class ModelEntityInDB(BaseModel):
    id: UUID
    name: str
    user_id: UUID
    description: str


class ModelEntityImplementationInDB(BaseModel):
    id: UUID
    model_id: UUID
    config: dict
    weights_save_dir: Optional[str] = None
    pipeline_id: Optional[UUID] = None
    created_at: datetime
    updated_at: datetime


class ModelFunctionInDB(BaseModel):
    id: UUID
    docstring: str
    args_schema: dict
    default_args: dict
    output_variables_schema: dict
    created_at: datetime
    updated_at: datetime


class ModelFunctionInputObjectGroupDefinitionInDB(BaseModel):
    id: UUID
    name: str
    required: bool
    function_id: UUID
    structure_id: str
    description: str
    created_at: datetime
    updated_at: datetime


class ModelFunctionOutputObjectGroupDefinitionInDB(BaseModel):
    id: UUID
    function_id: UUID
    name: Optional[str] = None
    structure_id: str
    description: str
    created_at: datetime
    updated_at: datetime


class ModelEntityFromPipelineInDB(BaseModel):
    pipeline_id: UUID
    model_entity_id: UUID
    created_at: datetime
    updated_at: datetime


class ModelSourceInDB(BaseModel):
    id: UUID
    type: SUPPORTED_MODEL_SOURCES_TYPE
    name: str
    description: str
    created_at: datetime
    updated_at: datetime


class PypiModelSourceInDB(BaseModel):
    id: UUID
    package_name: str
    package_version: str
    created_at: datetime
    updated_at: datetime


# API models

class ModelImplementationWithoutEmbedding(BaseModel):
    id: UUID
    definition_id: UUID
    version: int
    python_class_name: str
    description: str
    newest_update_description: str
    user_id: UUID
    source_id: UUID
    model_class_docstring: str
    training_function_id: UUID
    inference_function_id: UUID
    default_config: dict
    config_schema: dict
    created_at: datetime
    updated_at: datetime


class ModelFunction(ModelFunctionInDB):
    input_object_groups: List[ModelFunctionInputObjectGroupDefinitionInDB]
    output_object_groups: List[ModelFunctionOutputObjectGroupDefinitionInDB]


class ModelImplementation(ModelImplementationWithoutEmbedding):
    definition: ModelDefinitionInDB
    training_function: ModelFunction
    inference_function: ModelFunction
    implementation_script: ScriptInDB
    setup_script: Optional[ScriptInDB] = None
    description_for_agent: str


class ModelEntityImplementation(ModelEntityImplementationInDB):
    model_implementation: ModelImplementation


class ModelEntity(ModelEntityInDB):
    implementation: Optional[ModelEntityImplementation] = None
    description_for_agent: str


class GetModelEntityByIDsRequest(BaseModel):
    model_entity_ids: List[UUID]


class ModelSource(ModelSourceInDB):
    type_fields: Union[PypiModelSourceInDB]  # TODO: Add github


# Create models


class ModelFunctionInputObjectGroupDefinitionCreate(BaseModel):
    structure_id: str
    name: str
    description: str
    required: bool


class ModelFunctionOutputObjectGroupDefinitionCreate(BaseModel):
    structure_id: str
    name: Optional[str] = None
    description: str


class ModelFunctionCreate(BaseModel):
    docstring: str
    args_schema: dict
    default_args: dict
    output_variables_schema: dict
    input_object_groups: List[ModelFunctionInputObjectGroupDefinitionCreate]
    output_object_groups: List[ModelFunctionOutputObjectGroupDefinitionCreate]


class PypiModelSourceCreate(BaseModel):
    package_name: str
    package_version: str
    type: Literal["pypi"] = "pypi"


class ModelSourceCreate(BaseModel):
    type: SUPPORTED_MODEL_SOURCES_TYPE
    description: str
    name: str
    type_fields: PypiModelSourceCreate


class ModelImplementationCreate(BaseModel):
    name: str
    python_class_name: str
    public: bool
    description: str
    modality: SUPPORTED_MODALITIES_TYPE
    task: SUPPORTED_TASK_TYPE
    source: ModelSourceCreate
    model_class_docstring: str
    training_function: ModelFunctionCreate
    inference_function: ModelFunctionCreate
    default_config: dict
    config_schema: dict
    implementation_script_create: ScriptCreate
    setup_script_create: Optional[ScriptCreate] = None


class ModelEntityCreate(BaseModel):
    name: str
    description: str


class ModelEntityImplementationCreate(BaseModel):
    config: dict
    weights_save_dir: Optional[str] = None
    pipeline_id: Optional[UUID] = None
    model_implementation_id: Optional[UUID] = None
    model_implementation_create: Optional[ModelImplementationCreate] = None
    model_entity_id: Optional[UUID] = None
    model_entity_create: Optional[ModelEntityCreate] = None

    @model_validator(mode='after')
    def validate_model_specification(self):
        if self.model_implementation_id is None and self.model_implementation_create is None:
            raise ValueError(
                "Either model_id or model_create must be provided")
        if self.model_implementation_id is not None and self.model_implementation_create is not None:
            raise ValueError(
                "Only one of model_id or model_create can be provided, not both")
        return self

    @model_validator(mode='after')
    def validate_model_entity_specification(self):
        if self.model_entity_id is None and self.model_entity_create is None:
            raise ValueError(
                "Either model_entity_id or model_entity_create must be provided")
        if self.model_entity_id is not None and self.model_entity_create is not None:
            raise ValueError(
                "Only one of model_entity_id or model_entity_create can be provided, not both")
        return self


# Update models


class ModelFunctionUpdateCreate(BaseModel):
    docstring: Optional[str] = None
    args_schema: Optional[dict] = None
    output_variables_schema: Optional[dict] = None
    default_args: Optional[dict] = None
    input_object_groups_to_add: Optional[List[ModelFunctionInputObjectGroupDefinitionCreate]] = None
    output_object_group_definitions_to_add: Optional[
        List[ModelFunctionOutputObjectGroupDefinitionCreate]] = None
    input_object_groups_to_remove: Optional[List[UUID]] = None
    output_object_group_definitions_to_remove: Optional[List[UUID]] = None


class ModelUpdateCreate(BaseModel):
    definition_id: UUID
    updates_made_description: str
    new_implementation_create: ScriptCreate
    updated_description: Optional[str] = None
    updated_python_class_name: Optional[str] = None
    updated_model_class_docstring: Optional[str] = None
    updated_default_config: Optional[dict] = None
    updated_training_function: Optional[ModelFunctionUpdateCreate] = None
    updated_inference_function: Optional[ModelFunctionUpdateCreate] = None
    updated_config_schema: Optional[dict] = None
    model_entities_to_update: Optional[List[UUID]] = None
    new_setup_create: Optional[ScriptCreate] = None


# Update models


class ModelEntityUpdate(BaseModel):
    name: Optional[str] = None
    description: Optional[str] = None


class ModelEntityConfigUpdate(BaseModel):
    config: dict
