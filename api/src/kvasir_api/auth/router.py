from fastapi import APIRouter, Depends, Response, HTTPException, Request
from fastapi.security import OAuth2PasswordRequestForm
from datetime import timedelta
from typing import Annotated

from kvasir_api.auth.service import (
    authenticate_user,
    create_token,
    create_user,
    google_login,
    get_current_user,
    get_refresh_token_from_cookie,
    decode_token,
    get_user_by_id,
    get_user_by_email,
    update_user_profile,
    get_registration_status
)
from kvasir_api.auth.schema import User, UserCreate, UserWithToken, GoogleUserLogin, UserProfileUpdate, RegistrationStatus
from kvasir_api.app_secrets import ACCESS_TOKEN_EXPIRE_MINUTES, REFRESH_TOKEN_EXPIRE_DAYS, DEV


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


@router.post("/signout")
async def signout(response: Response) -> dict:
    response.delete_cookie(
        key="refresh_token",
        httponly=True,
        secure=not DEV,
        samesite="strict"
    )
    return {"message": "Successfully signed out"}


@router.post("/register", response_model=User)
async def register(user_create: UserCreate) -> User:
    # Check if registration is open
    reg_status = await get_registration_status()
    if not reg_status.is_open:
        raise HTTPException(status_code=403, detail=reg_status.message)

    user = await create_user(user_create)
    return user


@router.post("/google-login", response_model=UserWithToken)
async def google_login_endpoint(google_user: GoogleUserLogin, response: Response) -> UserWithToken:
    # Check if registration is open (only for new users)
    existing_user = await get_user_by_email(google_user.email)
    if not existing_user:
        reg_status = await get_registration_status()
        if not reg_status.is_open:
            raise HTTPException(status_code=403, detail=reg_status.message)

    user = await google_login(google_user)

    access_token, access_token_expires_at = create_token(
        data={"sub": user.id},
        expires_delta=timedelta(minutes=ACCESS_TOKEN_EXPIRE_MINUTES)
    )

    refresh_token, _ = create_token(
        data={"sub": user.id},
        expires_delta=timedelta(days=REFRESH_TOKEN_EXPIRE_DAYS)
    )

    user_with_token = UserWithToken(
        access_token=access_token,
        token_type="bearer",
        token_expires_at=access_token_expires_at,
        **user.model_dump()
    )

    response.set_cookie(
        key="refresh_token",
        value=refresh_token,
        httponly=True,
        secure=not DEV,
        samesite="strict"
    )

    return user_with_token


@router.get("/current-user", response_model=User)
async def current_user(user: Annotated[User, Depends(get_current_user)]) -> User:
    return user


@router.patch("/update-profile", response_model=User)
async def update_profile(
    profile_data: UserProfileUpdate,
    user: Annotated[User, Depends(get_current_user)]
) -> User:
    updated_user = await update_user_profile(user.id, profile_data.affiliation, profile_data.role)
    return updated_user


@router.get("/registration-status", response_model=RegistrationStatus)
async def registration_status() -> RegistrationStatus:
    return await get_registration_status()
