from uuid import UUID
from typing import List, Union

from project_server.client import ProjectClient
from synesis_schemas.main_server import (
    DataSource,
    DataSourceInDB,
    DataSourceAnalysisInDB,
    DataSourceAnalysisCreate,
    TabularFileDataSourceCreate,
    TabularFileDataSourceInDB,
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


async def post_file_data_source(client: ProjectClient, file_data: bytes, filename: str) -> DataSourceInDB:
    response = await client.send_request("post", "/data-sources/file-data-source", data={
        "file": file_data,
        "filename": filename
    })
    return DataSourceInDB(**response.body)


async def post_data_source_analysis(client: ProjectClient, analysis: DataSourceAnalysisCreate) -> DataSourceAnalysisInDB:
    response = await client.send_request("post", "/data-sources/data-source-analysis", json=analysis.model_dump(mode="json"))
    return DataSourceAnalysisInDB(**response.body)


async def post_data_source_details(client: ProjectClient, details: TabularFileDataSourceCreate) -> Union[TabularFileDataSourceInDB]:
    response = await client.send_request("post", "/data-sources/data-source-details", json=details.model_dump(mode="json"))
    return TabularFileDataSourceInDB(**response.body)
