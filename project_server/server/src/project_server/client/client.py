import aiohttp
from typing import Literal, Optional
from attr import dataclass

from project_server.app_secrets import MAIN_SERVER_URL


@dataclass
class FileInput:
    filename: str
    file_data: bytes
    content_type: str


@dataclass
class ProjectClientResponse:
    status: int
    headers: dict
    body: dict
    content_type: str


class ProjectClient:

    def __init__(self, bearer_token: Optional[str] = None):
        self.bearer_token = bearer_token

    def set_bearer_token(self, bearer_token: str):
        self.bearer_token = bearer_token

    async def send_request(
        self,
        method: Literal["get", "post", "put", "delete", "patch"],
        path: str,
        data: Optional[dict] = None,
        json: Optional[dict] = None,
        files: Optional[list[FileInput]] = None,
        params: Optional[dict] = None,
        headers: dict = {}
    ) -> ProjectClientResponse:

        if self.bearer_token:
            headers["Authorization"] = f'Bearer {self.bearer_token}'

        async with aiohttp.ClientSession() as session:

            is_form_data = files or data
            if is_form_data:
                form_data = aiohttp.FormData()
                if files:
                    for file in files:
                        form_data.add_field("files", file.file_data,
                                            filename=file.filename, content_type=file.content_type)
                if data:
                    for key, value in data.items():
                        form_data.add_field(key, value)
            else:
                form_data = None

            async with session.request(method, f"{MAIN_SERVER_URL}{path}", headers=headers, data=form_data, json=json, params=params) as response:

                if response.status == 401:
                    raise RuntimeError("Unauthorized")

                if response.status != 200:
                    raise RuntimeError(
                        f"Error {response.status}: {await response.text()}")

                return ProjectClientResponse(
                    status=response.status,
                    headers=dict(response.headers),
                    # We assume the response is json, maybe should be more robust
                    body=await response.json(),
                    content_type=response.headers.get('content-type', '')
                )
