from datetime import datetime
from pydantic import BaseModel, EmailStr
from typing import Optional
from uuid import UUID


class UserBase(BaseModel):
    username: str
    email: Optional[EmailStr] = None
    full_name: Optional[str] = None
    disabled: bool = False


class UserCreate(UserBase):
    password: str


class User(UserBase):
    id: UUID
    created_at: datetime
    updated_at: datetime


class UserInDB(User):
    hashed_password: str


class Token(BaseModel):
    access_token: str
    token_type: str


class TokenData(BaseModel):
    username: str | None = None


class UserAPIKey(BaseModel):
    id: UUID
    user_id: UUID
    key: str
    expires_at: datetime
    created_at: datetime | None = None
    updated_at: datetime | None = None
