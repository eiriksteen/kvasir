from fastapi import APIRouter, HTTPException

from synesis_api.modules.waitlist.schema import WaitlistCreate, WaitlistInDB
from synesis_api.modules.waitlist.service import create_waitlist_entry


router = APIRouter()


@router.post("/join", response_model=WaitlistInDB)
async def join_waitlist(
    request: WaitlistCreate,
) -> WaitlistInDB:
    """
    Add a new entry to the waitlist.
    Returns 400 if email already exists.
    """
    return await create_waitlist_entry(request)
