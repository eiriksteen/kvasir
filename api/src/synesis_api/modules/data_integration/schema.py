from uuid import UUID
from typing import List, Optional
from synesis_api.base_schema import BaseSchema


class LocalDirectoryFile(BaseSchema):
    id: UUID
    file_name: str
    file_path: str
    file_type: str
    description: str


class LocalDirectoryDataSource(BaseSchema):
    id: UUID
    directory_name: str
    save_path: str
    description: Optional[str] = None
    files: List[LocalDirectoryFile]


class IntegrationJobResult(BaseSchema):
    job_id: UUID
    dataset_id: UUID
    code_explanation: str


class IntegrationJobResultInDB(IntegrationJobResult):
    python_code_path: str


class IntegrationJobLocalInput(BaseSchema):
    job_id: UUID
    data_description: str
    data_directory_paths: List[str]
