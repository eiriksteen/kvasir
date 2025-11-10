from uuid import UUID
from typing import List

from project_server.client import ProjectClient
from synesis_schemas.main_server import (
    DataSource,
    DataSourceCreate,
    DataSourceDetailsCreate,
    GetDataSourcesByIDsRequest
)


async def get_data_sources(client: ProjectClient) -> List[DataSource]:
    response = await client.send_request("get", "/data-sources/data-sources")
    return [DataSource(**ds) for ds in response.body]


async def get_data_source(client: ProjectClient, data_source_id: UUID) -> DataSource:
    response = await client.send_request("get", f"/data-sources/data-source/{data_source_id}")
    return DataSource(**response.body)


async def get_data_sources_by_ids(client: ProjectClient, request: GetDataSourcesByIDsRequest) -> List[DataSource]:
    response = await client.send_request("get", f"/data-sources/data-sources-by-ids", json=request.model_dump(mode="json"))
    return [DataSource(**ds) for ds in response.body]


async def post_data_source(client: ProjectClient, request: DataSourceCreate) -> DataSource:
    response = await client.send_request("post", "/data-sources/data-source", json=request.model_dump(mode="json"))
    return DataSource(**response.body)


async def post_data_source_details(client: ProjectClient, request: DataSourceDetailsCreate) -> DataSource:
    response = await client.send_request("post", "/data-sources/data-source-details", json=request.model_dump(mode="json"))
    return DataSource(**response.body)
