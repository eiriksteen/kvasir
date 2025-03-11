from typing import AsyncGenerator
from sqlalchemy import MetaData
from sqlalchemy.ext.asyncio import AsyncConnection, create_async_engine
from ..secrets import DATABASE_URL, DATABASE_POOL_SIZE, DATABASE_POOL_TTL, DATABASE_POOL_PRE_PING


engine = create_async_engine(
    DATABASE_URL,
    pool_size=DATABASE_POOL_SIZE,
    pool_recycle=DATABASE_POOL_TTL,
    pool_pre_ping=DATABASE_POOL_PRE_PING,
)

metadata = MetaData()


async def get_db_connection() -> AsyncGenerator[AsyncConnection, None]:
    connection = await engine.connect()
    try:
        yield connection
    finally:
        await connection.close()
