import asyncio
import asyncpg
import pandas as pd
from typing import Any
from io import StringIO, BytesIO
from sqlalchemy import (
    CursorResult,
    Insert,
    Select,
    Update,
)
from sqlalchemy.ext.asyncio import AsyncConnection
from synesis_api.database.core import engine, get_asyncpg_connection


async def fetch_one(
    select_query: Select | Insert | Update,
    connection: AsyncConnection | None = None,
    commit_after: bool = False,
) -> dict[str, Any] | None:
    if not connection:
        async with engine.connect() as connection:
            cursor = await _execute_query(select_query, connection, commit_after)
            return cursor.first()._asdict() if cursor.rowcount > 0 else None

    cursor = await _execute_query(select_query, connection, commit_after)
    return cursor.first()._asdict() if cursor.rowcount > 0 else None


async def fetch_all(
    select_query: Select | Insert | Update,
    connection: AsyncConnection | None = None,
    commit_after: bool = False,
) -> list[dict[str, Any]]:
    if not connection:
        async with engine.connect() as connection:
            cursor = await _execute_query(select_query, connection, commit_after)
            return [r._asdict() for r in cursor.all()]

    cursor = await _execute_query(select_query, connection, commit_after)
    return [r._asdict() for r in cursor.all()]


async def execute(
    query: Insert | Update,
    connection: AsyncConnection = None,
    commit_after: bool = False,
) -> None:
    if not connection:
        async with engine.connect() as connection:
            return await _execute_query(query, connection, commit_after)

    return await _execute_query(query, connection, commit_after)


async def _execute_query(
    query: Select | Insert | Update,
    connection: AsyncConnection,
    commit_after: bool = False,
) -> CursorResult:
    result = await connection.execute(query)
    if commit_after:
        await connection.commit()

    return result


async def insert_df(
    df: pd.DataFrame,
    table_name: str,
    schema_name: str,
    connection: asyncpg.Connection = None,
    chunk_size: int = 10000
) -> None:
    own_connection = False
    if not connection:
        connection = await get_asyncpg_connection()
        own_connection = True

    try:
        async with connection.transaction():
            for chunk in df.groupby(df.index // chunk_size):
                string_buffer = StringIO()
                chunk[1].to_csv(string_buffer, index=False, header=False)
                csv_data = string_buffer.getvalue().encode('utf-8')
                buffer = BytesIO(csv_data)

                await connection.copy_to_table(
                    table_name,
                    schema_name=schema_name,
                    source=buffer,
                    columns=list(df.columns),
                    format="csv"
                )
    finally:
        if own_connection:
            await connection.close()
