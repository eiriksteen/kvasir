import uuid
import jwt
import base64
from typing import Annotated
from jwt.exceptions import InvalidTokenError
from passlib.context import CryptContext
from sqlalchemy import insert, select
from datetime import datetime, timedelta, timezone
from fastapi import Depends, HTTPException, status, Request
from fastapi.security import OAuth2PasswordBearer, APIKeyHeader
from cryptography.hazmat.primitives import serialization
from cryptography.hazmat.primitives.asymmetric.types import (
    PrivateKeyTypes,
    PublicKeyTypes,
)

from synesis_schemas.main_server import User, UserInDB, TokenData, UserCreate, JWKSEntry, JWKSData
from synesis_api.auth.models import users
from synesis_api.modules.orchestrator.models import conversation
from synesis_api.modules.runs.models import run
from synesis_api.modules.data_objects.models import dataset, object_group, data_object
from synesis_api.modules.data_sources.models import data_source
from synesis_api.app_secrets import PRIVATE_KEY_FILE_PATH, PUBLIC_KEY_FILE_PATH
from synesis_api.database.service import fetch_one, execute, fetch_all


pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")
oauth2_scheme = OAuth2PasswordBearer(tokenUrl="login")
api_key_header = APIKeyHeader(name="X-API-Key", auto_error=False)


def load_es256_private_key() -> PrivateKeyTypes:
    with open(PRIVATE_KEY_FILE_PATH, "rb") as key:
        private_key = serialization.load_pem_private_key(
            key.read(), password=None)

        return private_key


def load_es256_public_key() -> PublicKeyTypes:
    with open(PUBLIC_KEY_FILE_PATH, "rb") as key:
        public_key = serialization.load_pem_public_key(key.read())
        return public_key


def get_jwks() -> JWKSData:
    public_key = load_es256_public_key()
    public_numbers = public_key.public_numbers()
    x = public_numbers.x.to_bytes(32, "big")
    y = public_numbers.y.to_bytes(32, "big")
    x_b64 = base64.b64encode(x).decode("utf-8")
    y_b64 = base64.b64encode(y).decode("utf-8")

    jwks_entry = JWKSEntry(kid="1",
                           kty="EC",
                           alg="ES256",
                           use="sig",
                           crv="P-256",
                           x=x_b64,
                           y=y_b64)

    jwks_data = JWKSData(keys=[jwks_entry])

    return jwks_data


def verify_password(plain_password: str, hashed_password: str) -> bool:
    return pwd_context.verify(plain_password, hashed_password)


def get_password_hash(password: str) -> str:
    return pwd_context.hash(password)


async def get_user_by_email(email: str) -> UserInDB | None:
    user = await fetch_one(select(users).where(users.c.email == email))
    if user:
        return UserInDB(**user)
    return None


async def get_user_by_id(user_id: uuid.UUID) -> UserInDB | None:
    user = await fetch_one(select(users).where(users.c.id == user_id))
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

    secret_key = load_es256_private_key()
    secret_key_bytes = secret_key.private_bytes(
        serialization.Encoding.PEM, serialization.PrivateFormat.PKCS8, serialization.NoEncryption())
    to_encode.update({"exp": expire})
    encoded_jwt = jwt.encode(to_encode,
                             secret_key_bytes,
                             algorithm="ES256")

    return encoded_jwt, expire


def decode_token(token: str) -> TokenData:
    credentials_exception = HTTPException(
        status_code=status.HTTP_401_UNAUTHORIZED,
        detail="Could not validate credentials",
        headers={"WWW-Authenticate": "Bearer"},
    )
    try:
        public_key = load_es256_public_key()
        public_key_bytes = public_key.public_bytes(
            serialization.Encoding.PEM, serialization.PublicFormat.SubjectPublicKeyInfo)
        payload = jwt.decode(token,
                             public_key_bytes,
                             algorithms=["ES256"])
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
                    created_at=datetime.now(timezone.utc),
                    updated_at=datetime.now(timezone.utc))
    await execute(insert(users).values(user.model_dump()), commit_after=True)
    return user


async def user_owns_runs(user_id: uuid.UUID, run_ids: list[uuid.UUID]) -> bool:
    run_records = await fetch_all(select(run).where(run.c.id.in_(run_ids), run.c.user_id == user_id))
    return len(run_records) == len(run_ids)


async def user_owns_conversation(user_id: uuid.UUID, conversation_id: uuid.UUID) -> bool:
    conversation_record = await fetch_one(select(conversation).where(conversation.c.id == conversation_id, conversation.c.user_id == user_id))
    return conversation_record is not None


async def user_owns_dataset(user_id: uuid.UUID, dataset_id: uuid.UUID) -> bool:
    dataset_record = await fetch_one(select(dataset).where(dataset.c.id == dataset_id, dataset.c.user_id == user_id))
    return dataset_record is not None


async def user_owns_object_group(user_id: uuid.UUID, object_group_id: uuid.UUID) -> bool:

    object_group_record = await fetch_one(
        select(dataset).join(object_group).where(object_group.c.id ==
                                                 object_group_id, dataset.c.user_id == user_id)
    )

    return object_group_record is not None


async def user_owns_time_series(user_id: uuid.UUID, time_series_id: uuid.UUID) -> bool:
    owner_id = await fetch_one(select(
        dataset.c.user_id
    ).join(
        object_group,
        dataset.c.id == object_group.c.dataset_id
    ).join(
        data_object,
        object_group.c.id == data_object.c.group_id
    ).where(
        data_object.c.id == time_series_id
    ))

    return owner_id["user_id"] == user_id


async def user_owns_data_source(user_id: uuid.UUID, data_source_id: uuid.UUID) -> bool:
    data_source_record = await fetch_one(select(data_source).where(data_source.c.id == data_source_id, data_source.c.user_id == user_id))
    return data_source_record is not None
