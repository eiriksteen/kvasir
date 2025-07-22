from fastapi import APIRouter
from synesis_api.auth.schema import User
from synesis_api.auth.service import get_current_user, user_owns_dataset


router = APIRouter()


# TODO: Make this work with the new data objects
