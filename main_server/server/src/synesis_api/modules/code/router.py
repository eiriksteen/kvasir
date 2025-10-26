from fastapi import APIRouter, Depends, HTTPException
from typing import Annotated
from uuid import UUID

from synesis_api.auth.service import oauth2_scheme
from synesis_api.modules.code.service import get_scripts
from synesis_api.client import MainServerClient, get_raw_script
from synesis_schemas.main_server import ScriptWithRawCode

router = APIRouter()


@router.get("/script/{script_id}", response_model=ScriptWithRawCode)
async def get_script(
    script_id: UUID,
    token_data: Annotated[dict, Depends(oauth2_scheme)] = None
) -> ScriptWithRawCode:
    """Get a script by ID with raw code from project server"""
    try:
        # Get script metadata from database
        script_records = await get_scripts([script_id])
        if not script_records:
            raise HTTPException(status_code=404, detail="Script not found")

        script_record = script_records[0]

        # Get raw code from project server
        client = MainServerClient(token_data)
        raw_code = await get_raw_script(client, script_record.path)

        # Return script with raw code
        return ScriptWithRawCode(
            **script_record.model_dump(),
            code=raw_code
        )
    except Exception as e:
        raise HTTPException(
            status_code=500, detail=f"Failed to get script: {str(e)}")
