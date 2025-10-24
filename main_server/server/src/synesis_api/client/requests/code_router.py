import uuid

from synesis_api.client import MainServerClient


async def get_raw_script(client: MainServerClient, file_path: str) -> str:
    response = await client.send_request("get", f"/code/script?file_path={file_path}")
    return response.body
