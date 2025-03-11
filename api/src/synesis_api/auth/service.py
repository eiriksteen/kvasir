import uuid
import jwt
from typing import Annotated
from jwt.exceptions import InvalidTokenError
from passlib.context import CryptContext
from sqlalchemy import Insert, Select, Delete
from datetime import datetime, timedelta, timezone
from fastapi import Depends, HTTPException, status, Security
from fastapi.security import OAuth2PasswordBearer, APIKeyHeader
from .schema import User, UserInDB, TokenData, UserAPIKey
from .models import users, user_api_keys
from ..secrets import API_SECRET_KEY, API_SECRET_ALGORITHM
from ..database.service import fetch_one, execute


pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")
oauth2_scheme = OAuth2PasswordBearer(tokenUrl="token")
api_key_header = APIKeyHeader(name="X-API-Key", auto_error=False)


def verify_password(plain_password, hashed_password):
    return pwd_context.verify(plain_password, hashed_password)


def get_password_hash(password: str) -> str:
    return pwd_context.hash(password)


async def get_user(username: str) -> UserInDB | None:
    user = await fetch_one(Select(users).where(users.c.username == username))
    if user:
        return UserInDB(**user)
    return None


async def authenticate_user(username: str, password: str) -> User:
    user = await get_user(username)
    if not user:
        raise HTTPException(status_code=404, detail="User not found")
    if not verify_password(password, user.hashed_password):
        raise HTTPException(status_code=401, detail="Incorrect password")
    return user


def create_access_token(data: dict, expires_delta: timedelta | None = None) -> str:
    to_encode = data.copy()
    if expires_delta:
        expire = datetime.now(timezone.utc) + expires_delta
    else:
        expire = datetime.now(timezone.utc) + timedelta(minutes=15)
    to_encode.update({"exp": expire})
    encoded_jwt = jwt.encode(to_encode,
                             API_SECRET_KEY,
                             algorithm=API_SECRET_ALGORITHM)
    return encoded_jwt


async def get_current_user(token: Annotated[str, Depends(oauth2_scheme)]) -> UserInDB:
    credentials_exception = HTTPException(
        status_code=status.HTTP_401_UNAUTHORIZED,
        detail="Could not validate credentials",
        headers={"WWW-Authenticate": "Bearer"},
    )
    try:
        payload = jwt.decode(token,
                             API_SECRET_KEY,
                             algorithms=[API_SECRET_ALGORITHM])
        username = payload.get("sub")
        if username is None:
            raise credentials_exception
        token_data = TokenData(username=username)
    except InvalidTokenError:
        raise credentials_exception
    user = await get_user(token_data.username)
    if user is None:
        raise credentials_exception
    return user


async def create_user(username: str, password: str) -> UserInDB:
    user = await get_user(username)
    if user:
        raise HTTPException(status_code=400, detail="Username already exists")

    hashed_password = get_password_hash(password)
    user_id = uuid.uuid4()
    user = UserInDB(id=user_id,
                    username=username,
                    hashed_password=hashed_password,
                    created_at=datetime.now(timezone.utc).replace(tzinfo=None),
                    updated_at=datetime.now(timezone.utc).replace(tzinfo=None))
    await execute(Insert(users).values(user.model_dump()), commit_after=True)
    return user


async def create_api_key(current_user: UserInDB) -> UserAPIKey:
    expiration_time = (datetime.now(timezone.utc) +
                       timedelta(minutes=15)).replace(tzinfo=None)

    key_id = uuid.uuid4()
    api_key = UserAPIKey(id=key_id,
                         user_id=current_user.id,
                         key=uuid.uuid4().hex,
                         expires_at=expiration_time)

    await execute(Insert(user_api_keys).values(id=key_id,
                                               user_id=current_user.id,
                                               key=api_key.key,
                                               expires_at=expiration_time), commit_after=True)
    return api_key


async def get_api_key(current_user: UserInDB) -> UserAPIKey:

    api_key = await fetch_one(Select(user_api_keys).where(user_api_keys.c.user_id == current_user.id))

    if api_key is None:
        raise HTTPException(status_code=401, detail="No API key found")

    api_key = UserAPIKey(**api_key)

    if api_key.expires_at < datetime.now(timezone.utc).replace(tzinfo=None):
        await delete_api_key(current_user)
        raise HTTPException(status_code=401, detail="API key has expired")

    return api_key


async def delete_api_key(current_user: UserInDB) -> None:
    await execute(Delete(user_api_keys).where(user_api_keys.c.user_id == current_user.id), commit_after=True)


async def get_user_from_api_key(api_key: str = Security(api_key_header)) -> UserInDB:
    if api_key is None:
        return None

    api_key_data = await fetch_one(Select(user_api_keys).where(user_api_keys.c.key == api_key))
    if api_key_data is None:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid API key",
            headers={"WWW-Authenticate": "Bearer"},
        )

    if api_key_data["expires_at"] < datetime.now(timezone.utc).replace(tzinfo=None):
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="API key has expired",
            headers={"WWW-Authenticate": "Bearer"},
        )

    user = await fetch_one(Select(users).where(users.c.id == api_key_data["user_id"]))
    if user is None:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="User not found",
            headers={"WWW-Authenticate": "Bearer"},
        )

    return UserInDB(**user)
