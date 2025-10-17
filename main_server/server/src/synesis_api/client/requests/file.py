import uuid

from synesis_api.client import MainServerClient
from synesis_schemas.main_server import FileSavedResponse


async def post_file(client: MainServerClient, file: bytes, id: uuid.UUID) -> FileSavedResponse:
    response = await client.send_request("post", "/file/file", data={"file": file, "id": str(id)})
    return FileSavedResponse(**response.body)
