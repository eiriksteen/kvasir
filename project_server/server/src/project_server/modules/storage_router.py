from typing import Annotated
from fastapi import APIRouter, UploadFile, Form, File, Depends
from uuid import UUID

from synesis_schemas.project_server import FileSavedAPI
from project_server.entity_manager import file_manager
from project_server.auth import TokenData, decode_token


router = APIRouter()


@router.post("/file", response_model=FileSavedAPI)
async def file_data_source(
    file: UploadFile = File(...),
    id: UUID = Form(...),
    _: Annotated[TokenData, Depends(decode_token)] = None
) -> FileSavedAPI:

    file_content = await file.read()
    file_path = file_manager.save_raw_data_file(
        id, file.filename, file_content)
    file_saved = FileSavedAPI(file_id=id, file_path=str(file_path))

    return file_saved

    #
