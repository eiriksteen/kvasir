import aiohttp
from typing import Literal, Optional
from attr import dataclass

from synesis_api.app_secrets import PROJECT_SERVER_URL


@dataclass
class FileInput:
    field_name: str
    filename: str
    file_data: bytes
    content_type: str


@dataclass
class MainServerClientResponse:
    status: int
    headers: dict
    body: bytes | dict  # Can be bytes for files or dict for JSON
    content_type: str


class MainServerClient:

    def __init__(self, bearer_token: str):
        self.bearer_token = bearer_token
        self.refresh_tries = 0
        self.max_refresh_tries = 3

    async def send_request(
            self,
            method: Literal["get", "post", "put", "delete"],
            path: str,
            data: Optional[dict] = None,
            json: Optional[dict] = None,
            files: Optional[list[FileInput]] = None,
            headers: dict = {}) -> MainServerClientResponse:

        headers["Authorization"] = f'Bearer {self.bearer_token}'

        async with aiohttp.ClientSession() as session:

            is_form_data = files or data
            if is_form_data:
                form_data = aiohttp.FormData()
                if files:
                    for file in files:
                        form_data.add_field(file.field_name, file.file_data,
                                            filename=file.filename, content_type=file.content_type)
                if data:
                    for key, value in data.items():
                        form_data.add_field(key, value)
            else:
                form_data = None

            async with session.request(method, f"{PROJECT_SERVER_URL}{path}", headers=headers, data=form_data, json=json) as response:

                if response.status == 401:
                    if self.refresh_tries >= self.max_refresh_tries:
                        raise RuntimeError("Max tries reached")

                    else:
                        self.refresh_tries += 1
                        return await self.send_request(method, path, data, json, files, headers)

                elif response.status != 200:
                    raise RuntimeError(
                        f"Error {response.status}: {await response.text()}")

                # Check content type to determine how to read the body
                content_type = response.headers.get('content-type', '')
                if 'application/json' in content_type:
                    body = await response.json()
                else:
                    # For other content types (like images), read as bytes
                    body = await response.read()
                
                return MainServerClientResponse(
                    status=response.status,
                    headers=dict(response.headers),
                    body=body,
                    content_type=content_type
                )
