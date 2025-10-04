import uuid
from typing import List
from sqlalchemy import select, insert, update, delete
from synesis_api.database.service import execute, fetch_one, fetch_all
from synesis_api.modules.tables.models import tables
from synesis_schemas.main_server import BaseTable, TableCreate, TableUpdate


async def get_table_by_id(table_id: uuid.UUID) -> BaseTable | None:
    result = await fetch_one(select(tables).where(tables.c.id == table_id))
    if result is None:
        return None
    return BaseTable(**result)

async def create_table(table_create: TableCreate) -> BaseTable:
    table_id = uuid.uuid4()
    table = BaseTable(
        id=table_id,
        **table_create.model_dump()
    )

    await execute(insert(tables).values(**table.model_dump()), commit_after=True)

    table = await get_table_by_id(table_id)
    return table

async def update_table(table_update: TableUpdate) -> BaseTable:
    await execute(update(tables).where(tables.c.id == table_update.id).values(**table_update.model_dump()), commit_after=True)

    table = await get_table_by_id(table_update.id)
    return table

async def delete_table(table_id: uuid.UUID) -> None:
    await execute(delete(tables).where(tables.c.id == table_id), commit_after=True)

async def get_tables_by_analysis_result_id(analysis_result_id: uuid.UUID) -> List[BaseTable]:
    result = await fetch_all(select(tables).where(tables.c.analysis_result_id == analysis_result_id))
    return [BaseTable(**table) for table in result]