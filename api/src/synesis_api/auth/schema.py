from uuid import UUID
from datetime import datetime
from pydantic import EmailStr
from ..base_schema import BaseSchema


class UserBase(BaseSchema):
    email: EmailStr
    name: str
    disabled: bool = False


class UserCreate(UserBase):
    password: str


class User(UserBase):
    id: UUID
    created_at: datetime
    updated_at: datetime


class UserInDB(User):
    hashed_password: str


class UserWithToken(User):
    access_token: str
    token_type: str
    token_expires_at: datetime
    # TODO: add refresh_token


class TokenData(BaseSchema):
    user_id: str


class UserAPIKey(BaseSchema):
    id: UUID
    user_id: UUID
    key: str
    expires_at: datetime
    created_at: datetime | None = None
    updated_at: datetime | None = None
