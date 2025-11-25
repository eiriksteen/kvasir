import uuid
from datetime import datetime, timezone
from sqlalchemy import insert, select
from sqlalchemy.exc import IntegrityError
from fastapi import HTTPException

from synesis_api.database.service import execute, fetch_one
from synesis_api.modules.waitlist.models import waitlist
from synesis_api.modules.waitlist.schema import WaitlistCreate, WaitlistInDB


async def create_waitlist_entry(waitlist_data: WaitlistCreate) -> WaitlistInDB:
    """
    Create a new waitlist entry.
    Raises HTTPException if email already exists.
    """
    waitlist_obj = WaitlistInDB(
        id=uuid.uuid4(),
        **waitlist_data.model_dump(),
        created_at=datetime.now(timezone.utc)
    )

    try:
        await execute(
            insert(waitlist).values(waitlist_obj.model_dump()),
            commit_after=True
        )
    except IntegrityError:
        raise HTTPException(
            status_code=400,
            detail="Email already registered on waitlist"
        )

    return waitlist_obj
