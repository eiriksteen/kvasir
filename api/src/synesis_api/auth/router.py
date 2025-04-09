from fastapi import APIRouter, Depends, Response, HTTPException, Request
from fastapi.security import OAuth2PasswordRequestForm
from typing import Annotated
from .service import (
    authenticate_user,
    create_token,
    create_user,
    get_current_user,
    get_refresh_token_from_cookie,
    decode_token,
    get_user_by_id
)
from .schema import User, UserCreate, UserWithToken
from synesis_api.secrets import ACCESS_TOKEN_EXPIRE_MINUTES, REFRESH_TOKEN_EXPIRE_DAYS, DEV
from datetime import timedelta


router = APIRouter()


@router.post("/login", response_model=UserWithToken)
async def login_for_access_token(form_data: Annotated[OAuth2PasswordRequestForm, Depends()], response: Response) -> UserWithToken:
    user = await authenticate_user(form_data.username, form_data.password)

    access_token, access_token_expires_at = create_token(
        data={"sub": user.id},
        expires_delta=timedelta(minutes=ACCESS_TOKEN_EXPIRE_MINUTES)
    )

    refresh_token, _ = create_token(
        data={"sub": user.id},
        expires_delta=timedelta(days=REFRESH_TOKEN_EXPIRE_DAYS)
    )

    user_with_token = UserWithToken(access_token=access_token,
                                    token_type="bearer",
                                    token_expires_at=access_token_expires_at,
                                    **user.model_dump())

    response.set_cookie(key="refresh_token", value=refresh_token,
                        httponly=True, secure=not DEV, samesite="strict")

    return user_with_token


@router.post("/refresh", response_model=UserWithToken)
async def refresh_token(request: Request) -> UserWithToken:

    refresh_token = get_refresh_token_from_cookie(request)
    if refresh_token is None:
        raise HTTPException(status_code=401, detail="Refresh token not found")

    decoded_token = decode_token(refresh_token)
    user = await get_user_by_id(decoded_token.user_id)
    if user is None:
        raise HTTPException(status_code=401, detail="User not found")

    access_token, access_token_expires_at = create_token(
        data={"sub": user.id},
        expires_delta=timedelta(minutes=ACCESS_TOKEN_EXPIRE_MINUTES)
    )

    user_with_token = UserWithToken(access_token=access_token,
                                    token_type="bearer",
                                    token_expires_at=access_token_expires_at,
                                    **user.model_dump())

    return user_with_token


@router.post("/register", response_model=User)
async def register(user_create: UserCreate) -> User:
    user = await create_user(user_create)
    return user


@router.get("/current-user", response_model=User)
async def current_user(user: Annotated[User, Depends(get_current_user)]) -> User:
    return user
