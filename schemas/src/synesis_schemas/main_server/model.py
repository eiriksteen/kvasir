from pydantic import BaseModel
from typing import Optional, Literal, List
from datetime import datetime
from uuid import UUID


from .code import ScriptCreate, ScriptInDB


SUPPORTED_MODALITIES_TYPE = Literal["time_series", "tabular", "multimodal",
                                    "image", "text", "audio", "video"]


SUPPORTED_TASK_TYPE = Literal["forecasting", "classification", "regression",
                              "clustering", "anomaly_detection", "generation", "segmentation"]

FUNCTION_TYPE = Literal["training", "inference"]


# DB models

class ModelDefinitionInDB(BaseModel):
    id: UUID
    name: str
    modality: SUPPORTED_MODALITIES_TYPE
    task: SUPPORTED_TASK_TYPE
    public: bool
    created_at: datetime
    updated_at: datetime


class ModelInDB(BaseModel):
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


class ModelEntityInDB(BaseModel):
    id: UUID
    name: str
    user_id: UUID
    description: str
    model_id: UUID
    config: dict
    weights_save_dir: Optional[str] = None
    pipeline_id: Optional[UUID] = None
    created_at: datetime
    updated_at: datetime


class ModelEntityFromPipelineInDB(BaseModel):
    pipeline_id: UUID
    model_entity_id: UUID
    created_at: datetime
    updated_at: datetime


# API models

class ModelWithoutEmbedding(BaseModel):
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


class ModelFunctionFull(ModelFunctionInDB):
    input_object_groups: List[ModelFunctionInputObjectGroupDefinitionInDB]
    output_object_groups: List[ModelFunctionOutputObjectGroupDefinitionInDB]


class Model(ModelWithoutEmbedding):
    definition: ModelDefinitionInDB
    training_function: ModelFunctionFull
    inference_function: ModelFunctionFull
    implementation_script: ScriptInDB
    setup_script: Optional[ScriptInDB] = None


class ModelEntity(ModelEntityInDB):
    model: Model


class ModelDefinitionBare(BaseModel):
    id: UUID
    name: str


class ModelFunctionBare(BaseModel):
    id: UUID
    docstring: str


class ModelBare(BaseModel):
    id: UUID
    description: str
    config_schema: dict
    python_class_name: str
    model_class_docstring: str
    training_function: ModelFunctionBare
    inference_function: ModelFunctionBare
    definition: ModelDefinitionBare


class ModelEntityBare(BaseModel):
    id: UUID
    name: str
    description: str
    model: ModelBare


class GetModelEntityByIDsRequest(BaseModel):
    model_entity_ids: List[UUID]


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


class ModelCreate(BaseModel):
    name: str
    python_class_name: str
    public: bool
    description: str
    modality: SUPPORTED_MODALITIES_TYPE
    task: SUPPORTED_TASK_TYPE
    source_id: UUID
    model_class_docstring: str
    training_function: ModelFunctionCreate
    inference_function: ModelFunctionCreate
    default_config: dict
    config_schema: dict
    implementation_script_create: ScriptCreate
    setup_script_create: Optional[ScriptCreate] = None


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


class ModelEntityCreate(BaseModel):
    name: str
    description: str
    model_id: UUID
    config: dict
    weights_save_dir: Optional[str] = None
    pipeline_id: Optional[UUID] = None


# Update models

class ModelEntityConfigUpdate(BaseModel):
    config: dict
