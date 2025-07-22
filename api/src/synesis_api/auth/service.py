import uuid
import jwt
from typing import Annotated
from jwt.exceptions import InvalidTokenError
from passlib.context import CryptContext
from sqlalchemy import Insert, Select, Delete
from datetime import datetime, timedelta, timezone
from fastapi import Depends, HTTPException, status, Security, Request
from fastapi.security import OAuth2PasswordBearer, APIKeyHeader
from synesis_api.auth.schema import User, UserInDB, TokenData, UserAPIKey, UserCreate
from synesis_api.auth.models import users, user_api_keys
from synesis_api.modules.chat.models import conversations
from synesis_api.modules.jobs.models import job
from synesis_api.modules.data_objects.models import dataset
from synesis_api.secrets import API_SECRET_KEY, API_SECRET_ALGORITHM
from synesis_api.database.service import fetch_one, execute


pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")
oauth2_scheme = OAuth2PasswordBearer(tokenUrl="login")
api_key_header = APIKeyHeader(name="X-API-Key", auto_error=False)


def verify_password(plain_password: str, hashed_password: str) -> bool:
    return pwd_context.verify(plain_password, hashed_password)


def get_password_hash(password: str) -> str:
    return pwd_context.hash(password)


async def get_user_by_email(email: str) -> UserInDB | None:
    user = await fetch_one(Select(users).where(users.c.email == email))
    if user:
        return UserInDB(**user)
    return None


async def get_user_by_id(user_id: uuid.UUID) -> UserInDB | None:
    user = await fetch_one(Select(users).where(users.c.id == user_id))
    if user:
        return UserInDB(**user)
    return None


async def authenticate_user(email: str, password: str) -> User:
    user = await get_user_by_email(email)
    if not user:
        raise HTTPException(status_code=404, detail="User not found")
    if not verify_password(password, user.hashed_password):
        raise HTTPException(status_code=401, detail="Incorrect password")
    return user


def create_token(data: dict, expires_delta: timedelta | None = None) -> tuple[str, datetime]:

    assert "sub" in data, "subject must be provided"

    if isinstance(data["sub"], uuid.UUID):
        data["sub"] = str(data["sub"])

    to_encode = data.copy()

    if expires_delta:
        expire = datetime.now(timezone.utc) + expires_delta
    else:
        expire = datetime.now(timezone.utc) + timedelta(minutes=15)

    to_encode.update({"exp": expire})
    encoded_jwt = jwt.encode(to_encode,
                             API_SECRET_KEY,
                             algorithm=API_SECRET_ALGORITHM)

    return encoded_jwt, expire


def decode_token(token: str) -> dict:
    credentials_exception = HTTPException(
        status_code=status.HTTP_401_UNAUTHORIZED,
        detail="Could not validate credentials",
        headers={"WWW-Authenticate": "Bearer"},
    )
    try:
        payload = jwt.decode(token,
                             API_SECRET_KEY,
                             algorithms=[API_SECRET_ALGORITHM])
        user_id = payload.get("sub")
        if user_id is None:
            raise credentials_exception
        token_data = TokenData(user_id=user_id)
    except InvalidTokenError:
        raise credentials_exception
    return token_data


def get_refresh_token_from_cookie(request: Request) -> str | None:
    refresh_token = request.cookies.get("refresh_token")
    if refresh_token is None:
        return None
    return refresh_token


async def get_current_user(token: Annotated[str, Depends(oauth2_scheme)]) -> UserInDB:
    token_data = decode_token(token)
    user = await get_user_by_id(token_data.user_id)
    if user is None:
        raise HTTPException(status_code=401, detail="User not found")
    return user


async def create_user(user_create: UserCreate) -> UserInDB:
    user = await get_user_by_email(user_create.email)
    if user:
        raise HTTPException(status_code=400, detail="Email already exists")

    hashed_password = get_password_hash(user_create.password)
    user_id = uuid.uuid4()
    user = UserInDB(id=user_id,
                    email=user_create.email,
                    name=user_create.name,
                    hashed_password=hashed_password,
                    created_at=datetime.now(timezone.utc).replace(tzinfo=None),
                    updated_at=datetime.now(timezone.utc).replace(tzinfo=None))
    await execute(Insert(users).values(user.model_dump()), commit_after=True)
    return user


async def create_api_key(user: UserInDB) -> UserAPIKey:
    expiration_time = (datetime.now(timezone.utc) +
                       timedelta(minutes=15)).replace(tzinfo=None)

    key_id = uuid.uuid4()
    api_key = UserAPIKey(id=key_id,
                         user_id=user.id,
                         key=uuid.uuid4().hex,
                         expires_at=expiration_time)
    await execute(Insert(user_api_keys).values(id=key_id,
                                               user_id=user.id,
                                               key=api_key.key,
                                               expires_at=expiration_time), commit_after=True)
    return api_key


async def get_api_key(user: UserInDB) -> UserAPIKey:

    api_key = await fetch_one(Select(user_api_keys).where(user_api_keys.c.user_id == user.id))

    if api_key is None:
        raise HTTPException(status_code=401, detail="No API key found")

    api_key = UserAPIKey(**api_key)

    if api_key.expires_at < datetime.now(timezone.utc).replace(tzinfo=None):
        await delete_api_key(user)
        raise HTTPException(status_code=401, detail="API key has expired")

    return api_key


async def delete_api_key(user_id: uuid.UUID) -> None:
    await execute(Delete(user_api_keys).where(user_api_keys.c.user_id == user_id), commit_after=True)


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


async def user_owns_job(user_id: uuid.UUID, job_id: uuid.UUID) -> bool:
    job = await fetch_one(Select(job).where(job.c.id == job_id, job.c.user_id == user_id))
    return job is not None


async def user_owns_conversation(user_id: uuid.UUID, conversation_id: uuid.UUID) -> bool:
    conversation = await fetch_one(Select(conversations).where(conversations.c.id == conversation_id, conversations.c.user_id == user_id))
    return conversation is not None


async def user_owns_dataset(user_id: uuid.UUID, dataset_id: uuid.UUID) -> bool:
    dataset = await fetch_one(Select(dataset).where(dataset.c.id == dataset_id, dataset.c.user_id == user_id))
    return dataset is not None
