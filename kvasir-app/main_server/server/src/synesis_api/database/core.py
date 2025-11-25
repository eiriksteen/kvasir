import asyncpg
from typing import AsyncGenerator
from sqlalchemy import MetaData
from sqlalchemy.ext.asyncio import AsyncConnection, create_async_engine
from synesis_api.app_secrets import (
    DATABASE_URL,
    DATABASE_POOL_SIZE,
    DATABASE_POOL_TTL,
    DATABASE_POOL_PRE_PING,
    DB_USER,
    DB_PASSWORD,
    DB_HOST,
    DB_PORT,
    DB_NAME,
)

engine = create_async_engine(
    DATABASE_URL,
    pool_size=DATABASE_POOL_SIZE,
    pool_recycle=DATABASE_POOL_TTL,
    pool_pre_ping=DATABASE_POOL_PRE_PING,
)

naming_convention = {
    "ix": "ix_%(column_0_label)s",
    "uq": "uq_%(table_name)s_%(column_0_name)s",
    #   "ck": "ck_%(table_name)s", # I am not sure if this is correct, it does not seem unique?
    "fk": "fk_%(table_name)s_%(column_0_name)s_%(referred_table_name)s",
    "pk": "pk_%(table_name)s"
}

metadata = MetaData(naming_convention=naming_convention)


async def get_db_connection() -> AsyncGenerator[AsyncConnection, None]:
    connection = await engine.connect()
    try:
        yield connection
    finally:
        await connection.close()


async def get_asyncpg_connection() -> asyncpg.Pool:
    con = await asyncpg.connect(user=DB_USER, password=DB_PASSWORD, host=DB_HOST, port=DB_PORT, database=DB_NAME)
    return con
