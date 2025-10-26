from fastapi import APIRouter, Depends
from typing import Annotated

from project_server.auth import TokenData, decode_token
from project_server.entity_manager import script_manager


router = APIRouter()


@router.get("/script")
async def get_script_endpoint(
        file_path: str,
        token_data: Annotated[TokenData, Depends(decode_token)] = None) -> str:
    # TODO: Auth

    return script_manager.get_script(file_path)
