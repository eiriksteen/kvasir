from uuid import UUID
from datetime import datetime
from typing import List, Union, Literal, Optional, Dict, Any
from pydantic import BaseModel


DATA_SOURCE_TYPE_LITERAL = Literal["tabular_file", "key_value_file"]


# DB Models

class DataSourceInDB(BaseModel):
    id: UUID
    user_id: UUID
    type: DATA_SOURCE_TYPE_LITERAL
    name: str
    created_at: datetime


class TabularFileDataSourceInDB(BaseModel):
    id: UUID
    file_name: str
    file_path: str
    file_type: str
    file_size_bytes: int
    num_rows: int
    num_columns: int
    json_schema: Dict[str, Any]
    created_at: datetime
    updated_at: datetime
    content_preview: str


class KeyValueFileDataSourceInDB(BaseModel):
    id: UUID
    file_name: str
    file_path: str
    file_type: str
    file_size_bytes: int
    created_at: datetime
    updated_at: datetime


class DataSourceAnalysisInDB(BaseModel):
    id: UUID
    data_source_id: UUID
    content_description: str
    quality_description: str
    eda_summary: str
    cautions: str
    created_at: datetime
    updated_at: datetime


# API Models


# We include data source in db for the cases where the analysis agent hasn't yet finished the analysis to create the full data source object
# DataSource = Union[DataSourceInDB, TabularFileDataSource]

class DataSource(DataSourceInDB):
    # Add more possibilities here, and todo make non-optional
    type_fields: Union[TabularFileDataSourceInDB, KeyValueFileDataSourceInDB]
    analysis: Optional[DataSourceAnalysisInDB] = None
    description_for_agent: str


class GetDataSourcesByIDsRequest(BaseModel):
    data_source_ids: List[UUID]


# Create models


class TabularFileDataSourceCreate(BaseModel):
    name: str
    file_name: str
    file_path: str
    file_type: str
    file_size_bytes: int
    json_schema: Dict[str, Any]
    num_rows: int
    num_columns: int
    content_preview: str


class KeyValueFileDataSourceCreate(BaseModel):
    name: str
    file_name: str
    file_path: str
    file_type: str
    file_size_bytes: int


class DataSourceAnalysisCreate(BaseModel):
    data_source_id: UUID
    content_description: str
    quality_description: str
    eda_summary: str
    cautions: str
