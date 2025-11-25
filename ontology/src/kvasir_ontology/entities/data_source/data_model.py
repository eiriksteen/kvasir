from uuid import UUID
from datetime import datetime
from typing import List, Union, Literal, Optional, Dict, Any, Type
from pydantic import BaseModel, field_validator
from pathlib import Path


DATA_SOURCE_TYPE_LITERAL = Literal["file"]


class DataSourceBase(BaseModel):
    id: UUID
    user_id: UUID
    type: DATA_SOURCE_TYPE_LITERAL
    name: str
    description: Optional[str] = None
    additional_variables: Optional[Dict[str, Any]] = None
    created_at: datetime
    updated_at: datetime


class FileDataSourceBase(BaseModel):
    id: UUID
    file_name: str
    file_path: str
    file_type: str
    file_size_bytes: int
    created_at: datetime
    updated_at: datetime


class DataSource(DataSourceBase):
    # Add more possibilities here
    # Optional until agent has filled it (we want the data source to show up right away so we allow it to be null until then)
    type_fields: Optional[Union[FileDataSourceBase]] = None


# Create models


class UnknownFileCreate(BaseModel):
    """"
    This is for file types not covered by the other file create schemas. 
    It is for any type we haven't added yet. 
    NB: The file path must be an absolute path!
    """
    name: str
    file_name: str
    file_path: str
    file_type: str
    file_size_bytes: int

    @field_validator('file_path')
    @classmethod
    def validate_absolute_path(cls, v):
        if not Path(v).is_absolute():
            raise ValueError('file_path must be an absolute path')
        return v

    class Config:
        extra = "allow"


class TabularFileCreate(UnknownFileCreate):
    """"
    This is for tabular files, including csv, parquet, excel, etc. 
    """
    json_schema: str
    pandas_df_info: str
    pandas_df_head: str
    num_rows: int
    num_columns: int
    missing_fraction_per_column: str
    iqr_anomalies_fraction_per_column: str

    class Config:
        extra = "allow"


class DataSourceCreate(BaseModel):
    """"
    Create a data source. 
    The name should reflect the actual source, for example files should be the file name including the extension.
    """
    name: str
    description: str
    type: DATA_SOURCE_TYPE_LITERAL
    type_fields: Optional[Union[UnknownFileCreate, TabularFileCreate]] = None
    # In addition to general extra info, this can be used to store info about "wildcard" sources that we don't have dedicated tables for
    # We don't need to create fill the tables below

    class Config:
        extra = "allow"


class DataSourceDetailsCreate(BaseModel):
    data_source_id: UUID
    type_fields: Union[UnknownFileCreate, TabularFileCreate]

    class Config:
        extra = "allow"
