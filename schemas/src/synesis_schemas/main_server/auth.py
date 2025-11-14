from uuid import UUID
from datetime import datetime
from pydantic import EmailStr, BaseModel


class UserBase(BaseModel):
    email: EmailStr
    name: str
    affiliation: str = "Unknown"
    role: str = "Unknown"
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


class TokenData(BaseModel):
    user_id: str


class UserAPIKey(BaseModel):
    id: UUID
    user_id: UUID
    key: str
    expires_at: datetime
    created_at: datetime | None = None
    updated_at: datetime | None = None


class JWKSEntry(BaseModel):
    kid: str
    kty: str
    alg: str
    use: str
    crv: str
    x: bytes
    y: bytes


class JWKSData(BaseModel):
    keys: list[JWKSEntry]
