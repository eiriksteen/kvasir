from synesis_api.client import MainServerClient, FileInput
from synesis_schemas.main_server import TabularFileDataSourceCreate, KeyValueFileDataSourceCreate


async def post_tabular_file_data_source(
    client: MainServerClient,
    file_data: bytes,
    filename: str,
    content_type: str
) -> TabularFileDataSourceCreate:
    file_input = FileInput(
        field_name="file",
        filename=filename,
        file_data=file_data,
        content_type=content_type
    )
    response = await client.send_request("post", "/data-source/tabular-file", files=[file_input])
    return TabularFileDataSourceCreate(**response.body)


async def post_key_value_file_data_source(
    client: MainServerClient,
    file_data: bytes,
    filename: str,
    content_type: str
) -> KeyValueFileDataSourceCreate:
    file_input = FileInput(
        field_name="file",
        filename=filename,
        file_data=file_data,
        content_type=content_type
    )
    response = await client.send_request("post", "/data-source/key-value-file", files=[file_input])
    return KeyValueFileDataSourceCreate(**response.body)
