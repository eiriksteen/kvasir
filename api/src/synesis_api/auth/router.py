import uuid
from fastapi import APIRouter, Depends
from fastapi.security import OAuth2PasswordRequestForm
from typing import Annotated
from .service import authenticate_user, create_access_token, create_user, get_current_user
from .schema import Token, User, UserCreate
from synesis_api.secrets import ACCESS_TOKEN_EXPIRE_MINUTES
from datetime import timedelta


router = APIRouter()


@router.post("/token", response_model=Token)
async def login_for_access_token(form_data: Annotated[OAuth2PasswordRequestForm, Depends()]) -> Token:
    user = await authenticate_user(form_data.username, form_data.password)
    access_token_expires = timedelta(minutes=ACCESS_TOKEN_EXPIRE_MINUTES)
    access_token = create_access_token(
        data={"sub": user.username}, expires_delta=access_token_expires)
    return Token(access_token=access_token, token_type="bearer")


@router.post("/register", response_model=User)
async def register(user: UserCreate) -> User:
    user = await create_user(user.username, user.password)
    return user


@router.get("/current-user", response_model=User)
async def current_user(user: Annotated[User, Depends(get_current_user)]) -> User:
    return user
