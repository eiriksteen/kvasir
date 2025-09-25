import jwt
import base64
from cryptography.hazmat.primitives.asymmetric import ec
from cryptography.hazmat.primitives import serialization
from cryptography.hazmat.primitives.asymmetric.types import PublicKeyTypes
from fastapi.security import OAuth2PasswordBearer
from jwt.exceptions import InvalidTokenError
from fastapi import HTTPException, status
from fastapi import Depends
from typing import Annotated
from pydantic import BaseModel

from project_server.redis import get_redis
from project_server.client import ProjectClient, get_jwks
from project_server.app_secrets import MAIN_SERVER_URL


oauth2_scheme = OAuth2PasswordBearer(tokenUrl=f"{MAIN_SERVER_URL}/auth/login")


class TokenData(BaseModel):
    user_id: str
    bearer_token: str


async def load_es256_public_key() -> PublicKeyTypes:
    # Try redis first, if doesnt exist, query /.well-known/jwks.json from main server
    redis = get_redis()
    redis_value = await redis.get(f"public_key")
    if redis_value:
        return redis_value
    else:
        # Query /.well-known/jwks.json from main server
        client = ProjectClient()
        jwks_record = await get_jwks(client)
        x_bytes = base64.b64decode(jwks_record.keys[0].x)
        y_bytes = base64.b64decode(jwks_record.keys[0].y)
        x = int.from_bytes(x_bytes, "big")
        y = int.from_bytes(y_bytes, "big")

        public_numbers = ec.EllipticCurvePublicNumbers(
            x=x,
            y=y,
            curve=ec.SECP256R1()
        )

        public_key = public_numbers.public_key()

        public_key_bytes = public_key.public_bytes(
            serialization.Encoding.PEM,
            serialization.PublicFormat.SubjectPublicKeyInfo
        )

        await redis.set(f"public_key", public_key_bytes)

        return public_key_bytes


async def decode_token(token: Annotated[str, Depends(oauth2_scheme)]) -> TokenData:
    credentials_exception = HTTPException(
        status_code=status.HTTP_401_UNAUTHORIZED,
        detail="Could not validate credentials",
        headers={"WWW-Authenticate": "Bearer"},
    )
    try:
        public_key_bytes = await load_es256_public_key()
        payload = jwt.decode(token,
                             public_key_bytes,
                             algorithms=["ES256"])
        user_id = payload.get("sub")
        if user_id is None:
            raise credentials_exception
        token_data = TokenData(user_id=user_id, bearer_token=token)
    except InvalidTokenError:
        raise credentials_exception

    return token_data
