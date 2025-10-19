import uuid
from datetime import datetime, timezone
from typing import List
from sqlalchemy import select
from synesis_schemas.main_server import ScriptCreate, ScriptInDB

from synesis_api.database.service import execute, fetch_all
from synesis_api.modules.code.models import script


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
    return [ScriptInDB(**s) for s in script_records]
