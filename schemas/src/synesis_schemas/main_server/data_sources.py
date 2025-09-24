from uuid import UUID
from datetime import datetime
from typing import List, Union, Literal, Optional
from pydantic import BaseModel

from .data_objects import FeatureInDB


# DB Models

class DataSourceInDB(BaseModel):
    id: UUID
    user_id: UUID
    type: Literal["file"]
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
    created_at: datetime
    updated_at: datetime
    content_preview: Optional[str] = None


class DataSourceAnalysisInDB(BaseModel):
    id: UUID
    data_source_id: UUID
    content_description: str
    quality_description: str
    eda_summary: str
    cautions: str
    created_at: datetime
    updated_at: datetime


class FeatureInTabularFileInDB(BaseModel):
    feature_name: str
    tabular_file_id: UUID
    created_at: datetime
    updated_at: datetime


# API Models


class TabularFileDataSource(DataSourceInDB, TabularFileDataSourceInDB):
    features: List[FeatureInDB]
    analysis: Optional[DataSourceAnalysisInDB] = None


# We include data source in db for the cases where the analysis agent hasn't yet finished the analysis to create the full data source object
DataSourceFull = Union[DataSourceInDB, TabularFileDataSource]


class DetailedDataSourceRecords(BaseModel):
    tabular_records: List[TabularFileDataSource]
    # TODO: Add other data source types here


class FileSavedResponse(BaseModel):
    file_id: UUID
    file_path: str


class GetDataSourcesByIDsRequest(BaseModel):
    data_source_ids: List[UUID]


# Create models


class DataSourceCreate(BaseModel):
    name: str
    type: str


class TabularFileDataSourceCreate(BaseModel):
    data_source_id: UUID
    file_name: str
    file_path: str
    file_type: str
    file_size_bytes: int
    num_rows: int
    num_columns: int
    content_preview: Optional[str] = None


class DataSourceAnalysisCreate(BaseModel):
    data_source_id: UUID
    content_description: str
    quality_description: str
    eda_summary: str
    cautions: str
