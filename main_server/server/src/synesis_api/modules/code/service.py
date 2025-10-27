import uuid
from datetime import datetime, timezone
from typing import List
from sqlalchemy import select
from fastapi import Depends

from synesis_api.auth.service import oauth2_scheme
from synesis_api.database.service import execute, fetch_all
from synesis_api.modules.code.models import script
from synesis_api.client import MainServerClient, get_raw_script
from synesis_schemas.main_server import ScriptCreate, ScriptInDB


async def create_script(user_id: uuid.UUID, script_create: ScriptCreate) -> ScriptInDB:
    script_record = ScriptInDB(
        id=uuid.uuid4(),
        user_id=user_id,
        **script_create.model_dump(),
        created_at=datetime.now(timezone.utc),
        updated_at=datetime.now(timezone.utc)
    )
    await execute(script.insert().values(script_record.model_dump()), commit_after=True)
    return script_record


async def get_scripts(script_ids: List[uuid.UUID]) -> List[ScriptInDB]:
    script_query = select(script).where(script.c.id.in_(script_ids))
    script_records = await fetch_all(script_query)
    script_objs = [
        ScriptInDB(**script_record) for script_record in script_records
    ]

    return script_objs
