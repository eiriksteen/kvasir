import uuid
from typing import List


from project_server.client import ProjectClient
from synesis_schemas.main_server import BaseTable, TableCreate, TableUpdate


async def create_table(client: ProjectClient, table_create: TableCreate) -> BaseTable:
    response = await client.send_request("post", "/analysis/table", json=table_create.model_dump(mode="json"))
    return BaseTable(**response.body)


async def update_table(client: ProjectClient, table_id: uuid.UUID, table_update: TableUpdate) -> BaseTable:
    response = await client.send_request("put", f"/analysis/table/{table_id}", json=table_update.model_dump(mode="json"))
    return BaseTable(**response.body)


async def delete_table(client: ProjectClient, table_id: uuid.UUID) -> dict:
    response = await client.send_request("delete", f"/analysis/table/{table_id}")
    return response.body


async def get_tables_by_analysis_result_id(client: ProjectClient, analysis_result_id: uuid.UUID) -> List[BaseTable]:
    response = await client.send_request("get", f"/analysis/table/analysis-result/{analysis_result_id}")
    return [BaseTable(**table) for table in response.body]
