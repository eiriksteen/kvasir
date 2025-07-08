from uuid import UUID
from datetime import datetime
from typing import Dict, Any, List, Optional
from synesis_api.base_schema import BaseSchema
from synesis_api.modules.ontology.schema import JobMetadata


class Modality(BaseSchema):
    id: UUID
    name: str
    description: Optional[str]


class Task(BaseSchema):
    id: UUID
    name: str
    description: Optional[str]
    created_at: datetime


class Source(BaseSchema):
    id: UUID
    name: str
    description: Optional[str]
    created_at: datetime


class ProgrammingLanguage(BaseSchema):
    id: UUID
    name: str
    description: Optional[str]
    created_at: datetime


class ProgrammingLanguageVersion(BaseSchema):
    id: UUID
    programming_language_id: UUID
    version: str
    created_at: datetime


class Model(BaseSchema):
    id: UUID
    name: str
    description: str
    input_description: str
    output_description: str
    config_parameters: List[str]
    created_at: datetime
    public: bool


class ModelInDB(Model):
    owner_id: UUID
    modality_id: UUID
    setup_script_path: str
    config_script_path: str
    source_id: UUID
    programming_language_version_id: UUID


class ModelTask(BaseSchema):
    id: UUID
    model_id: UUID
    task_id: UUID
    created_at: datetime


class ModelTaskInDB(ModelTask):
    inference_script_path: str
    training_script_path: str


class ModelJoined(Model):
    modality: Modality
    source: Source
    programming_language_version: ProgrammingLanguageVersion
    integration_jobs: List[JobMetadata] | None = None
    tasks: List[Task]
