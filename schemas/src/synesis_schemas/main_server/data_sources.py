from uuid import UUID
from datetime import datetime
from typing import List, Union, Literal, Optional, Dict, Any, Type
from pydantic import BaseModel


DATA_SOURCE_TYPE_LITERAL = Literal["file"]


# DB Models


class DataSourceInDB(BaseModel):
    id: UUID
    user_id: UUID
    type: DATA_SOURCE_TYPE_LITERAL
    name: str
    additional_variables: Optional[Dict[str, Any]] = None
    created_at: datetime


class FileDataSourceInDB(BaseModel):
    id: UUID
    file_name: str
    file_path: str
    file_type: str
    file_size_bytes: int
    created_at: datetime
    updated_at: datetime


class DataSourceFromPipelineInDB(BaseModel):
    data_source_id: UUID
    pipeline_id: UUID
    created_at: datetime
    updated_at: datetime


# API Models


class DataSource(DataSourceInDB):
    # Add more possibilities here
    # Optional until agent has filled it (we want the data source to show up right away so we allow it to be null until then)
    type_fields: Optional[Union[FileDataSourceInDB]] = None
    description_for_agent: str
    from_pipelines: List[UUID]


class GetDataSourcesByIDsRequest(BaseModel):
    data_source_ids: List[UUID]


# Create models


class UnknownFileCreate(BaseModel):
    """"
    This is for file types not covered by the other file create schemas. 
    It is for any type we haven't added yet. 
    """
    name: str
    file_name: str
    file_path: str
    file_type: str
    file_size_bytes: int

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
    name: str
    type: DATA_SOURCE_TYPE_LITERAL
    type_fields: Union[UnknownFileCreate, TabularFileCreate]
    from_pipelines: Optional[List[UUID]] = None
    # In addition to general extra info, this can be used to store info about "wildcard" sources that we don't have dedicated tables for
    # We don't need to create fill the tables below

    class Config:
        extra = "allow"


# Helpers
# Used to let the agent know the schemas it's data sources must abide by


class DataSourcesInDBInfo(BaseModel):
    in_db_model: Type[BaseModel]
    create_model: Type[BaseModel]
    in_db_table_name: str


def get_data_sources_in_db_info(type: DATA_SOURCE_TYPE_LITERAL, subtype: Optional[Literal["tabular"]] = None) -> DataSourcesInDBInfo:
    if type == "file":
        if subtype == "tabular":
            return DataSourcesInDBInfo(
                in_db_model=FileDataSourceInDB,
                # We specify some extra fields to add to additional_variables
                create_model=TabularFileCreate,
                in_db_table_name="file_data_source"
            )
        else:
            return DataSourcesInDBInfo(
                in_db_model=FileDataSourceInDB,
                create_model=UnknownFileCreate,
                in_db_table_name="file_data_source"
            )
    else:
        raise ValueError(f"Invalid data source type: {type}")
