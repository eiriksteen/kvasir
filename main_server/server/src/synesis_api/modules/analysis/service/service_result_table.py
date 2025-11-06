import uuid
from typing import List
from sqlalchemy import select, insert, delete
from fastapi import HTTPException

from synesis_api.database.service import execute, fetch_one, fetch_all
from synesis_api.modules.analysis.models import result_table
from synesis_schemas.main_server import ResultTableInDB, ResultTableCreate


async def create_result_table(table_create: ResultTableCreate) -> ResultTableInDB:
    """Create a new result table record."""
    table_id = uuid.uuid4()
    table_in_db = ResultTableInDB(
        id=table_id,
        **table_create.model_dump()
    )
    await execute(
        insert(result_table).values(**table_in_db.model_dump()),
        commit_after=True
    )

    return table_in_db


async def get_result_tables_by_analysis_result_id(analysis_result_id: uuid.UUID) -> List[ResultTableInDB]:
    """Get all result tables for a specific analysis result."""
    results = await fetch_all(
        select(result_table).where(
            result_table.c.analysis_result_id == analysis_result_id)
    )

    return [ResultTableInDB(**result) for result in results]


async def delete_result_table(table_id: uuid.UUID) -> bool:
    """Delete a result table by ID."""
    table_id = select(result_table).where(result_table.c.id == table_id)
    if table_id is None:
        return False

    await execute(
        delete(result_table).where(result_table.c.id == table_id),
        commit_after=True
    )

    return True
