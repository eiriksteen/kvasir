from uuid import UUID
from datetime import datetime
from typing import List, Optional, Union
from synesis_api.base_schema import BaseSchema
from synesis_api.modules.data_objects.schema import FeatureInDB


class DataSourceInDB(BaseSchema):
    id: UUID
    user_id: UUID
    type: str
    name: str
    description: Optional[str] = None
    quality_description: Optional[str] = None
    content_preview: Optional[str] = None
    created_at: datetime


class FileDataSourceInDB(BaseSchema):
    id: UUID
    file_name: str
    file_path: str
    file_type: str
    file_size_bytes: int
    created_at: datetime
    updated_at: datetime


class TabularFileDataSourceInDB(BaseSchema):
    id: UUID
    num_rows: int
    num_columns: int
    created_at: datetime
    updated_at: datetime


class FeatureInTabularFileInDB(BaseSchema):
    feature_name: str
    tabular_file_id: UUID
    created_at: datetime
    updated_at: datetime


class TabularFileDataSource(DataSourceInDB, FileDataSourceInDB, TabularFileDataSourceInDB):
    features: List[FeatureInDB]


DataSource = Union[TabularFileDataSource]
