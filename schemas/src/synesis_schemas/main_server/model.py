from pydantic import BaseModel
from typing import Optional, Literal, List
from datetime import datetime
from uuid import UUID


SUPPORTED_MODALITIES_TYPE = Literal["time_series", "tabular", "multimodal",
                                    "image", "text", "audio", "video"]


SUPPORTED_TASK_TYPE = Literal["forecasting", "classification", "regression",
                              "clustering", "anomaly_detection", "generation", "segmentation"]


# DB models

class ModelInDB(BaseModel):
    id: UUID
    name: str
    description: str
    owner_id: UUID
    public: bool
    modality: SUPPORTED_MODALITIES_TYPE
    source_id: UUID
    task: SUPPORTED_TASK_TYPE
    programming_language_with_version: str
    embedding: List[float]
    # For now, we have one task per model, meaning for example we have different models for XGBoostForecaster and XGBoostClassifier
    # We can make it more sophisticated by allowing for multiple tasks per model, and allow for multi task tuning etc
    inference_function_id: UUID
    training_function_id: UUID
    created_at: datetime
    updated_at: datetime
    setup_script_path: Optional[str] = None
    default_config: Optional[dict] = None


class ModelEntityInDB(BaseModel):
    id: UUID
    name: str
    description: str
    model_id: UUID
    created_at: datetime
    updated_at: datetime
    weights_save_dir: Optional[str] = None
    pipeline_id: Optional[UUID] = None
    project_id: Optional[UUID] = None
    config: Optional[dict] = None


class ModelEntityFromPipelineInDB(BaseModel):
    pipeline_id: UUID
    model_entity_id: UUID
    created_at: datetime
    updated_at: datetime


# API models

class ModelWithoutEmbedding(ModelInDB):
    id: UUID
    name: str
    description: str
    owner_id: UUID
    public: bool
    modality: SUPPORTED_MODALITIES_TYPE
    source_id: UUID
    task: SUPPORTED_TASK_TYPE
    programming_language_with_version: str
    inference_function_id: UUID
    training_function_id: UUID
    created_at: datetime
    updated_at: datetime
    setup_script_path: Optional[str] = None
    default_config: Optional[dict] = None


class ModelBare(BaseModel):
    id: UUID
    name: str
    description: str
    modality: SUPPORTED_MODALITIES_TYPE
    default_config: Optional[dict] = None


class ModelEntityFull(ModelEntityInDB):
    model: ModelWithoutEmbedding


# Create models


class ModelCreate(BaseModel):
    name: str
    public: bool
    description: str
    modality: SUPPORTED_MODALITIES_TYPE
    source_id: UUID
    programming_language_with_version: str
    inference_function_id: UUID
    training_function_id: UUID
    task: SUPPORTED_TASK_TYPE
    default_config: Optional[dict] = None


class ModelEntityCreate(BaseModel):
    name: str
    description: str
    model_id: UUID
    project_id: UUID
    weights_save_dir: Optional[str] = None
    pipeline_id: Optional[UUID] = None
    config: Optional[dict] = None
