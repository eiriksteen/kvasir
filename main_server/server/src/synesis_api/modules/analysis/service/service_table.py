import uuid
from typing import List
from sqlalchemy import select, insert, update, delete


from synesis_api.database.service import execute, fetch_one, fetch_all
from synesis_api.modules.analysis.models import result_table
from synesis_schemas.main_server import BaseTable, TableCreate, TableUpdate


async def get_table_by_id(table_id: uuid.UUID) -> BaseTable | None:
    result = await fetch_one(select(result_table).where(result_table.c.id == table_id))
    if result is None:
        return None
    return BaseTable(**result)


async def create_table(table_create: TableCreate) -> BaseTable:
    table_id = uuid.uuid4()
    table_in_db = BaseTable(
        id=table_id,
        **table_create.model_dump()
    )
    await execute(insert(result_table).values(**table_in_db.model_dump()), commit_after=True)

    table_in_db = await get_table_by_id(table_id)
    return table_in_db


async def update_table(table_update: TableUpdate) -> BaseTable:
    await execute(update(result_table).where(result_table.c.id == table_update.id).values(**table_update.model_dump()), commit_after=True)

    table_in_db = await get_table_by_id(table_update.id)
    return table_in_db


async def delete_table(table_id: uuid.UUID) -> None:
    await execute(delete(result_table).where(result_table.c.id == table_id), commit_after=True)


async def get_tables_by_analysis_result_id(analysis_result_id: uuid.UUID) -> List[BaseTable]:
    result = await fetch_all(select(result_table).where(result_table.c.analysis_result_id == analysis_result_id))
    return [BaseTable(**table) for table in result]
