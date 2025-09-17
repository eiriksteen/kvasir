from pydantic import BaseModel
from typing import Optional, Dict, Any, Literal
from datetime import datetime
from uuid import UUID


SUPPORTED_MODALITIES_TYPE = Literal["time_series", "tabular", "multimodal",
                                    "image", "text", "audio", "video"]

SUPPORTED_SOURCE_TYPE = Literal["github", "pypi", "gitlab",
                                "huggingface", "local"]


SUPPORTED_TASK_TYPE = Literal["forecasting", "classification", "regression",
                              "clustering", "anomaly_detection", "generation", "segmentation"]


class ModelInDB(BaseModel):
    id: UUID
    name: str
    description: str
    owner_id: UUID
    public: bool
    modality: SUPPORTED_MODALITIES_TYPE
    source: SUPPORTED_SOURCE_TYPE
    programming_language_with_version: str
    default_config: Dict[str, Any]
    created_at: datetime
    updated_at: datetime
    setup_script_path: Optional[str] = None


class ModelTaskInDB(BaseModel):
    model_id: UUID
    task: SUPPORTED_TASK_TYPE
    inference_function_id: UUID
    training_function_id: UUID
    created_at: datetime
    updated_at: datetime


class ModelResult(BaseModel):
    id: UUID
    description: str
    model_task_id: UUID
    weights_path: str
    created_at: datetime
    updated_at: datetime
    config: Optional[dict] = None
