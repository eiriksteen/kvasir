from typing import Annotated
from fastapi import APIRouter, UploadFile, Form, File, Depends
from uuid import UUID

from project_server.entity_manager import DataSourceManager
from project_server.auth import TokenData, decode_token
from synesis_schemas.main_server import TabularFileDataSourceCreate, FileDataSourceCreate


router = APIRouter()


@router.post("/tabular-file", response_model=TabularFileDataSourceCreate)
async def tabular_file_data_source(
    file: UploadFile = File(...),
    token_data: Annotated[TokenData, Depends(decode_token)] = None
) -> TabularFileDataSourceCreate:

    file_content = await file.read()
    data_source_manager = DataSourceManager(
        bearer_token=token_data.bearer_token)
    data_source_create = data_source_manager.save_tabular_file_source(
        file.filename, file_content)
    return data_source_create


@router.post("/key-value-file", response_model=FileDataSourceCreate)
async def key_value_file_data_source(
    file: UploadFile = File(...),
    token_data: Annotated[TokenData, Depends(decode_token)] = None
) -> FileDataSourceCreate:

    file_content = await file.read()
    data_source_manager = DataSourceManager(
        bearer_token=token_data.bearer_token)
    data_source_create = data_source_manager.save_key_value_file_source(
        file.filename, file_content)
    return data_source_create
