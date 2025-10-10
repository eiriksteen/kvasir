import uuid
from typing import List


from project_server.client import ProjectClient
from synesis_schemas.main_server import BaseTable, TableCreate, TableUpdate


async def create_table(client: ProjectClient, table_create: TableCreate) -> BaseTable:
    response = await client.send_request("post", "/create-table", json=table_create.model_dump(mode="json"))
    return BaseTable(**response.body)


async def update_table(client: ProjectClient, table_id: uuid.UUID, table_update: TableUpdate) -> BaseTable:
    response = await client.send_request("put", f"/update-table/{table_id}", json=table_update.model_dump(mode="json"))
    return BaseTable(**response.body)


async def delete_table(client: ProjectClient, table_id: uuid.UUID) -> dict:
    response = await client.send_request("delete", f"/delete-table/{table_id}")
    return response.body


async def get_tables_by_analysis_result_id(client: ProjectClient, analysis_result_id: uuid.UUID) -> List[BaseTable]:
    response = await client.send_request("get", f"/get-tables-by-analysis-result-id/{analysis_result_id}")
    return [BaseTable(**table) for table in response.body]
